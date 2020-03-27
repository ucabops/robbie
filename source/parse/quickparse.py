import argparse
import json
from pprint import pprint

from xwentry import CrosswordEntry
from xwpuzzle import Crossword
from xwset import CrosswordSet


def convert_to_str(entryset):
    output = ''
    for entry in entryset:
        solution = entry['underscored_solution']
        synonyms = entry['all_synonyms']
        if synonyms:
            output += solution
            for token in synonyms:
                output += f' {token}'
            output += '\n'
    return output


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
    
    # Save the extracted features as JSON
    filepath = f'./data/{args.filename}-entries.json'
    with open(filepath, 'w') as file:
        json.dump(d, file)
    print(f"Feature set #1 saved to {filepath}")
    
    # Create a train/test split from dataset
    ratio = 0.9
    train_len = round(ratio * len(d))
    test_len = len(d) - train_len
    
    train_data = []
    test_data = []
    for i, entry in enumerate(d.values()):
        if i < test_len:
            test_data.append(entry)
        else:
            train_data.append(entry)
    
    # Save the extracted features as TXT
    train_output = convert_to_str(train_data)
    test_output = convert_to_str(test_data)
    
    filepath = f'./data/{args.filename}-entries-train.txt'
    with open(filepath, 'w') as file:
        file.write(train_output)
    print(f"Feature set #2 (train) saved to {filepath}")

    filepath = f'./data/{args.filename}-entries-test.txt'
    with open(filepath, 'w') as file:
        file.write(test_output)
    print(f"Feature set #2 (test) saved to {filepath}")
    