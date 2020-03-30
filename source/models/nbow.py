import numpy as np
import pandas as pd
from tabulate import tabulate

from .util import *


def key_adder(w2v_model, wordpairs):
    """Account for as many cases of british vs. american spelling as possible
    in W2V vocabulary

    Args:
      w2v_model : standard Word2Vec 'KeyedVectors' data structure
      wordps    : dictionary of strings containing the british spelling of words spelt using american english

    """

    for i in range(len(wordpairs)):
        try:
            vec = w2v_model[wordpairs[i][1]]
            w2v_model.add(wordpairs[i][0], vec)
        except KeyError:
            # print(wordpairs[i][0])
            continue

    return w2v_model


def clue_vectorizer(w2v_model, clue_words, pooling):
    """Finds vector representation of clue, by mean/sum pooling and keep track of any clue words that 
    are not in the W2V model

    Args:
      w2v_model  : standard Word2Vec 'KeyedVectors' data structure
      clue_words : list of tokens representing clue
      pooling    : sum or mean

    """

    # Vector representation of clue
    clue_vec = np.zeros((300))
    clue_errors = []
    for word in clue_words:
            # Must account for words not in W2V's vocabulary (e.g. 'to')
        try:
            clue_vec += w2v_model[word].reshape((300))
        except KeyError:
            clue_errors.append(word)
            continue

    # Sum or mean pool
    if pooling == 'mean':
        clue_vec = clue_vec/(len(clue_words))
    elif pooling == 'sum':
        pass

    return clue_vec, clue_errors


def sol_tracker(w2v_model, solution):
    """Keep a record of those solution words that do not appear in the W2V vocabulary

    Args :
      w2v_model : standard Word2Vec 'KeyedVectors' data structure
      solution  : List of tokenised words representing solution

    """

    sol_errors = []
    for word in solution:
        # Must account for words not in W2V's vocabulary (e.g. 'to')
        try:
            _ = w2v_model[word]
        except KeyError:
            sol_errors.append(word)
            continue

    return sol_errors


def multi_synonym(w2v_model, multi_syns, n, pooling):
    """Given list of synonyms that represents crossword clue, return aggregate ranking

    Args:
      w2v_model  : standard Word2Vec 'KeyedVectors' data structure
      multi_syns : nested list containing lists of each synonym present in a clue
      n          : number of words to retreive from W2V model for each synonym
      pooling    : sum or mean

    """

    # Construct seperate vector representaion for each synoynm
    clue_vecs = []
    for synonym in multi_syns:
        cv, _ = clue_vectorizer(w2v_model, synonym, pooling=pooling)
        clue_vecs.append(cv)

    # Find words and corresponding scores of top n most likely answer candidates for  each synonym
    words = []
    scores = []
    for i in range(len(multi_syns)):
        top_n = w2v_model.similar_by_vector(
            clue_vecs[i], topn=n, restrict_vocab=None)
        top_list = [top_n[j][0].lower() for j in range(len(top_n))]
        score_list = [top_n[k][1] for k in range(len(top_n))]
        words.append(top_list)
        scores.append(score_list)

    # Retreive words common to all rankings
    int1 = words[0]
    for word_list in words[1:]:
        int1 = np.intersect1d(int1, word_list)

    # Contingency for no common words between the two retreived rankings
    if len(int1) == 0:
        return []

    # Retrieve scores corresponding to each intersection word in each of the original rankings
    scores_list = np.zeros(len(int1))
    for i in range(len(words)):
        indices = np.intersect1d(words[i], int1, return_indices=True)
        int_scores = np.take(scores[i], indices[1])
        scores_list += int_scores

    # Dictionary for intersection words and summed scores
    rank_dict = {}
    for A, B in zip(int1, scores_list):
        rank_dict[A] = B

    # Sort based on score in descending order and return word ranking
    sorted_x = dict(
        sorted(rank_dict.items(), key=lambda kv: kv[1], reverse=True))
    top_list = list(sorted_x.keys())

    return top_list


def master_base(w2v_model, data, pairs, pooling, version, topn, verbose,
                enhancements={'length': True,
                              'clue_word': True,
                              'anagrams': True,
                              'multi_synonym': True,
                              'multiword': True}):
    """Finds vector representations of clues and retreives 'topn' answer candidates from within W2V vocabulary 
    based on cosine similarity score. These answer candidates can then be filtered further using various 
    combinations of the boolean flags in the 'enhancements' argument, in order to return more accurate answer 
    candidates for each clue.

    Args : 
      w2v_model    : standard Word2Vec 'KeyedVectors' data structure
      data         : dict containing full dataset
      pairs        : List of keys to access in clue data structure
      pooling      : Mean or sum pooling 
      version      : 1 - Baseline, 
                     2 - Access to Enhancements,
      topn         : Retreive 'topn' answer candidates
      verbose      : 1 - see clue,answer,rank of correct answer 
                     2 - see the top 10 w2v answers also
      enhancements : Dictionary of constraints to consider. Set to True to activate.

    Output : 
      1) Metrics = [
                  Number of Correct answers in top 10, 
                  Number of Correct answers in top 100,
                  Ranks of correct answers in top 10,
                  Rank of correct asnwers in top 100
                  Number of correct answers at Rank 1,
                  Number of Correct answers in top 1000
      ]

      2) Errors = [
                  Clue words not in W2V vocab,
                  Solution words not in W2V vocab,
                  Keys of Clue for which Top 10 could not be retreived
                  Keys of Clue for which Top 100 could not be retreived
                  Keys of Clue for no answer candidates could be retreived
                  Key of Clue for which intersection of retreived answer candidates could not be found 
                  in the case of multi-syms constraint set to True

      ]

      3) Pairs  = Total number of Clues considered by model from current run      

    """

    # Retreive keys for current crossword
    keys = pairs
    count_10 = 0
    count_100 = 0
    count_1000 = 0
    rank_list100 = []
    rank_list1000 = []
    clue_errors = []
    sol_errors = []
    clue_track100 = []
    clue_track1000 = []
    rank1 = 0
    clue_track1 = []
    multi_clue_track = []
    pairs = 0

    # For all clues
    for key in keys:
        # Retreive clue and solution from dataframe
        clue, solution = data[key]['all_synonyms'], data[key]['tokenized_solution']
        if clue == None:
            continue

        '-----------------------------  Vector Representation of Clue --------------------------------- '

        # Clue vector representation
        clue_vec, c_errors = clue_vectorizer(w2v_model, clue, pooling=pooling)
        clue_errors.append(c_errors)

        # Solution words not in vocab
        s_errors = sol_tracker(w2v_model, solution)
        sol_errors.append(s_errors)

        '-----------------------------  Retreive Answer Candidates from W2V and Apply Filters --------------------------------- '
        # Retreive topn answer candidates
        top_100 = w2v_model.similar_by_vector(
            clue_vec, topn=topn, restrict_vocab=None)
        top_list = [top_100[i][0].lower() for i in range(len(top_100))]

        # Version 1
        if version == 1:
            pass

        # Version 2 - allow access to enhancements
        if version == 2:

            # Return aggregate of rankings for each synonym
            if len(data[key]['synonyms']) > 1 and enhancements['multi_synonym'] == True:
                multi_list = multi_synonym(
                    w2v_model, data[key]['synonyms'], n=100000, pooling=pooling)

                if len(multi_list) == 0:
                    #print("Sorry could not find any intersection between candidates returned for each synonym for clue :",key)
                    multi_clue_track.append(key)
                else:
                    top_list = multi_list

            # Filter out words in clue
            if enhancements['clue_word'] == True:
                top_l = word_remover(top_list, clue)
            else:
                top_l = top_list

            # Filter out words of incorrect length
            if enhancements['length'] == True:
                if enhancements['multiword'] != True:
                    top_list = len_filterer(
                        top_l, len(data[key]['pretty_solution']))
                elif enhancements['multiword'] == True:

                    # Filter by total length including spaces
                    top_l = pretty_len_filterer(
                        top_l, len(data[key]['pretty_solution']))

                    # Filter by individual word length
                    top_list = len_filterer_multi(
                        top_l, data[key]['token_lengths'])

            # Filter by anagram
            if enhancements['anagrams'] == True and data[key]['anagram'] != None:
                top_list = anagram_filterer(
                    top_list, data[key]['anagram'].lower())

        # Remove duplicates
        top_list = list(dict.fromkeys(top_list))

        if len(top_list) == 0:
            clue_track1.append(key)

        '-----------------------------  Record Filtered, Ranked Answer Candidates ---------------------------------'

        # Store word and score in dictionary
        top_words = {}
        top_100word = {}
        top_1000word = {}
        top_full = {}

        # Consider top 10 answer candidates
        for i in range(10):
            try:
                top_words.update({i+1: top_list[i]})

            except IndexError:
                # clue_track10.append(key)
                break

        # Consider top 100 answer candidates
        for i in range(100):
            try:
                top_100word.update({i+1: top_list[i]})
            except IndexError:
                clue_track100.append(key)
                break

        # Consider top 1000 answer candidates
        for i in range(1000):
            try:
                top_1000word.update({i+1: top_list[i]})
            except IndexError:
                clue_track1000.append(key)
                break

        for i in range(len(top_list)):
            top_full.update({i+1: top_list[i]})

        # Convert to dataframes
        top_df = pd.DataFrame.from_dict(
            top_words, orient='index', columns=['Word'])
        top_100df = pd.DataFrame.from_dict(
            top_100word, orient='index', columns=['Word'])
        top_1000df = pd.DataFrame.from_dict(
            top_1000word, orient='index', columns=['Word'])
        top_fulldf = pd.DataFrame.from_dict(
            top_full, orient='index', columns=['Word'])

        '----------------------------- Compute and Update Model Metrics --------------------------------- '
        # Split words by _ when multiword constraint is set to True
        if enhancements['multiword'] == True:
            # Check if solution contained in top 10/100/1000 or at all
            int_10 = [word for word in top_df['Word']
                      if re.split(r"[_]", word) == solution]
            int_100 = [word for word in top_100df['Word']
                       if re.split(r"[_]", word) == solution]
            int_1000 = [word for word in top_1000df['Word']
                        if re.split(r"[_]", word) == solution]
            int_full = [word for word in top_fulldf['Word']
                        if re.split(r"[_]", word) == solution]

        else:
            # Check if solution contained in top 10/100/1000 or at all
            int_10 = [word for word in top_df['Word'] if [word] == solution]
            int_100 = [word for word in top_100df['Word']
                       if [word] == solution]
            int_1000 = [word for word in top_1000df['Word']
                        if [word] == solution]
            int_full = [word for word in top_fulldf['Word']
                        if [word] == solution]

        # Update model modetrics
        if len(int_10) > 0:
            count_10 += 1
            sol_rank10 = top_df.index[top_df['Word'] == int_10[0]].tolist()[0]
            if sol_rank10 == 1:
                rank1 += 1

        if len(int_100) > 0:
            count_100 += 1
            sol_rank = top_100df.index[top_100df['Word'] == int_100[0]].tolist()[
                0]
            rank_list100.append(sol_rank)

        if len(int_1000) > 0:
            count_1000 += 1
            sol_rank1k = top_1000df.index[top_1000df['Word'] == int_1000[0]].tolist()[
                0]
            rank_list1000.append(sol_rank1k)
            ans_rank = sol_rank1k
        elif len(int_full) > 0:
            ans_rank = top_fulldf.index[top_fulldf['Word'] == int_full[0]].tolist()[
                0]
        else:
            ans_rank = str("could not find correct answer")

        pairs += 1

        # Print model output
        if verbose == 2:
            print(key)
            print("Clue :", data[key]['synonyms'])
            print("Answer: {}".format(solution))
            print("Rank of Correct Answer :", ans_rank)
            print("Top 10 W2V predictions :")
            print(tabulate(top_df, headers='keys', tablefmt='psql'))
            print("--------------------------------------------------------------------")
        elif verbose == 1:
            print(key)
            print("Clue :", data[key]['synonyms'])
            print("Answer: {}".format(solution))
            print("Rank of Correct Answer :", ans_rank)
            print("--------------------------------------------------------------------")

    metrics = [count_10, count_100, rank_list100,
               rank_list1000, rank1, count_1000]
    errors = [clue_errors, sol_errors, clue_track100,
              clue_track1000, clue_track1, multi_clue_track]

    return metrics, errors, pairs
