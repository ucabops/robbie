import argparse
import json
from pprint import pprint

from xwentry import CrosswordEntry
from xwpuzzle import Crossword
from xwset import CrosswordSet


if __name__ == '__main__':
    script_desc = 'Parse raw dataset of crosswords and extract useful features.'
    parser = argparse.ArgumentParser(description=script_desc)
    parser.add_argument('filename', type=str,
                        help='file where raw data is located, excluding \'.json\' extension. must be in \'./data/raw\'.')
    args = parser.parse_args()

    # Load the dataset
    filepath = f'./data/raw/{args.filename}.json'
    with open(filepath, 'r') as file:
        data = json.load(file)
    
    # Parse the dictionary of crosswords
    xwset = CrosswordSet.from_dict(data)
    
    # Extract relevant features
    d = {}
    for xw_id, xw in xwset:
        for entry_id, entry in xw.entries:
            info = {
                'solution': entry.solution,
                'pretty_solution': entry.pretty_solution,
                'underscored_solution': entry.underscored_solution,
                'tokenized_solution': entry.tokenized_solution,
                'token_lengths': entry.token_lengths,
                'synonyms': entry.synonyms,
                'all_synonyms': entry.all_synonyms,
                'anagram': entry.anagram,
            }
            d[f'{xw_id}-{entry_id}'] = info
    
    # Save the extracted features
    filepath = f'./data/{args.filename}-entries.json'
    with open(filepath, 'w') as file:
        json.dump(d, file)
