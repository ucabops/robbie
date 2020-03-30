import re
import numpy as np


def cos_sim(vec1, vec2):
    """Find cosine similarity score of two vector representations

    Args:
      vec1 : Word vector 1
      vec2 : Word vector 2

    """
    score = np.divide(np.dot(vec1.T, vec2),
                      (np.linalg.norm(vec1)*np.linalg.norm(vec2)))
    return score


def master_count(data, keys, num_pairs):
    """Counts number of single answers and multi word answers from a given
    list of clues

    Args:
      data      : dict containing full dataset
      keys      : list of clues
      num_pairs : number of clues from the list to consider

    """

    singles = 0
    multiples = 0

    for key in keys[0:num_pairs]:
        sol = data[key]['tokenized_solution']
        solution = [word.lower() for word in sol]
        if len(solution) == 1:
            singles += 1
        elif len(solution) > 1:
            multiples += 1

    total = singles + multiples

    return singles, multiples, total


def word_remover(wlist, clue_words):
    """Given list of words, removes any occurence of specified words

    Args :
      wlist      : List of words
      clue_words : Words to be removed from w2vlist

    """

    array = np.asarray(wlist)
    for word in clue_words:
        array = array[array != word]
    return array


def len_filterer(words, size):
    """Given a list of words, filters out those words whose length is not equal to that specified

    Args:
      words : List of words to filter
      size  : Words whose length will be used to filter

    """
    return list(filter(lambda x: len(x) == size, words))


def pretty_len_filterer(words, sol_length):
    """Filtering by length including underscore and space between words (in the case of multi word solutions) 
    before filtering by length of individual words seperate by underscore

    Args:
      words      : list of words to filter
      sol_length : lengthg os olution word t filter by

    """
    keep = []
    for word in words:
        if len(word) == sol_length:
            keep.append(word)
    return keep


def len_filterer_multi(words, sol_lens):
    """Filters out those words whose length is not equal to that specified by splitting them based on '_' 
    and returns only those that match the length of individual words before and after '_' in the answer.

    Args:
      words : List of words
      solution : Words whose length will be used to filter

    """

    keep = []

    for i in range(len(words)):
        split_words = re.split(r"[_]", words[i])
        split_lens = [len(subword) for subword in split_words]
        if np.array_equal(np.asarray(split_lens), np.asarray(sol_lens)):
            keep.append(words[i])

    return keep


def anagram_filterer(words, sol_anagram):
    """Filters out those words that are not anagrams of sol_anagram

    Args: 
      words: answer candidates returned by W2V model
      sol_anagram : word that other words must be an anagram of

    """

    keep = []
    for word in words:
        word = re.sub('_', '', word)
        if(sorted(word) == sorted(sol_anagram)):
            keep.append(word)

    return keep
