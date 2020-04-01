import argparse
import json
import os
import time
import urllib

import numpy as np
import pandas as pd
import gensim

from models.nbow import master_base, key_adder
from models.amer_brit import wordpairs


def print_metrics(metrics, runs):
    acc_at_1 = metrics[4]/runs
    acc_at_10 = metrics[0]/runs
    acc_at_100 = metrics[1]/runs
    
    correct_at_100 = metrics[1]
    correct_at_1000 = metrics[5]
    
    median_at_100 = np.median(np.asarray(metrics[2]))
    median_at_1000 = np.median(np.asarray(metrics[3]))
    
    print(f"Total Number of Clues Considered: {runs}")
    print(f"Accuracy @ Rank   1: {acc_at_1:.2%}")
    print(f"Accuracy @ Rank  10: {acc_at_10:.2%}")
    print(f"Accuracy @ Rank 100: {acc_at_100:.2%}")
    print(f"Number of Correct Answers in top 100: {correct_at_100}")
    print(f"Median answer rank, top 100: {median_at_100}")
    print(f"Number of Correct Answers in top 1000: {correct_at_1000}")
    print(f"Median answer rank, top 1000: {median_at_1000}")


if __name__ == '__main__':
    script_desc = 'Run the neural bag-of-words model (NBOW) on the \'gquick\' dataset'
    parser = argparse.ArgumentParser(description=script_desc)
    parser.add_argument('filename', type=str,
                        help='File where data is located, excluding \'*-entries.json\' suffix. Must be in \'./data\'')
    parser.add_argument('--variant', dest='variant', type=int, nargs=1, default=0,
                        help='Choose variant to run. Defaults to 0')
    args = parser.parse_args()
    
    # Load the dataset
    filepath = f'./data/{args.filename}-entries.json'
    with open(filepath, 'r') as file:
        data = json.load(file)
    
    # Download Google's pretrained W2V model
    w2v_path = './data/GoogleNews-vectors-negative300.bin.gz'
    if not os.path.isfile(w2v_path):
        print('Downloading the pre-trained W2V model (could take a while, grab a cup of tea...)')
        url = 'https://nlpcrossworddata.blob.core.windows.net/test/GoogleNews-vectors-negative300.bin.gz'
        urllib.request.urlretrieve(url, w2v_path)
    
    # Load W2V model into memory
    model = gensim.models.KeyedVectors.load_word2vec_format(w2v_path, binary=True)
    
    # Choose which BOW variant to run
    if args.variant == 0:
        enhancements = {'length': False,
                        'clue_word': False,
                        'anagrams': False,
                        'multi_synonym': False,
                        'spelling': False,
                        'multiword': False}
    elif args.variant == 1:
        enhancements = {'length': True,
                        'clue_word': False,
                        'anagrams': False,
                        'multi_synonym': False,
                        'spelling': False,
                        'multiword': False}
    elif args.variant == 2:
        enhancements = {'length': True,
                        'clue_word': True,
                        'anagrams': False,
                        'multi_synonym': False,
                        'spelling': False,
                        'multiword': False}
    elif args.variant == 3:
        enhancements = {'length': True,
                        'clue_word': True,
                        'anagrams': True,
                        'multi_synonym': False,
                        'spelling': False,
                        'multiword': False}
    elif args.variant == 4:
        enhancements = {'length': True,
                        'clue_word': True,
                        'anagrams': True,
                        'multi_synonym': True,
                        'spelling': False,
                        'multiword': False}
    elif args.variant == 5:
        enhancements = {'length': True,
                        'clue_word': True,
                        'anagrams': True,
                        'multi_synonym': True,
                        'spelling': True,
                        'multiword': False}
    elif args.variant == 6:
        enhancements = {'length': True,
                        'clue_word': True,
                        'anagrams': True,
                        'multi_synonym': False,
                        'spelling': True,
                        'multiword': False}
    elif args.variant == 7:
        enhancements = {'length': True,
                        'clue_word': True,
                        'anagrams': True,
                        'multi_synonym': True,
                        'spelling': True,
                        'multiword': True}
    elif args.variant == 8:
        enhancements = {'length': True,
                        'clue_word': True,
                        'anagrams': True,
                        'multi_synonym': False,
                        'spelling': True,
                        'multiword': True}
    else:
        msg = f'Unknown variant "{args.variant}" (must be between 0 and 8)'
        raise ValueError(msg)
    
    # Save current time. Used for metrics
    start_time = time.time()
    
    # Add embeddings for British spellings of words, if requested
    if enhancements['spelling']:
        model = key_adder(model, wordpairs)
        dur = time.time() - start_time
        print(f'British spellings added to model in {dur/60} mins.')
    
    # Run model
    keys = list(data.keys())
    metrics, errs, runs = master_base(model, data, keys, pooling='mean', version=2, topn=100000, verbose=2,
                                      enhancements={'length': True,
                                                    'clue_word': True,
                                                    'anagrams': True,
                                                    'multi_synonym': False,
                                                    'multiword': True})
    
    print_metrics(metrics, runs)
    end_time = time.time()
    print(f"Process finished --- {(end_time-start_time)/60:.1f} minutes ---")
