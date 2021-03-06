import argparse
import json

# List of corrections to apply
corrections = [
    {'xw': '10252', 'entry': '19-down', 'clue': 'Ponder (5)'},
    {'xw': '10445', 'entry': '19-across', 'clue': 'Baptist in Bible (4)'},
    {'xw': '11025', 'entry': '19-across', 'group': ['17-across']},
    {'xw': '11037', 'entry': '14-across', 'clue': 'Conjecture (6)'},
    {'xw': '11037', 'entry': '17-across', 'clue': 'City on River Severn (10)'},
    {'xw': '11038', 'entry': '19-across', 'clue': 'Paper - birthday, Christmas, etc. (4)'},
    {'xw': '11551', 'entry': '17-down', 'group': ['15-down']},
    {'xw': '11651', 'entry': '17-down', 'group': ['16-down']},
    {'xw': '11707', 'entry': '19-across', 'clue': 'Gunfire - attempt (4)'},
    {'xw': '11707', 'entry': '18-down', 'clue': 'Fewer (4)'},
    {'xw': '11873', 'entry': '19-across', 'group': ['16-across']},
]

# List of crosswords to ignore
broken_xws = [
    '10362',
]


# Convenience function for getting one entry from a set of crosswords.
def get_entry(data, xw_id, entry_id):
    if xw_id in data:
        xw = data[xw_id]
        for entry in xw['entries']:
            if entry['id'] == entry_id:
                return entry


if __name__ == '__main__':
    script_desc = 'Apply fixes to a downloaded set of crosswords.'
    parser = argparse.ArgumentParser(description=script_desc)
    parser.add_argument('filename', type=str,
                        help='file where data is located, excluding \'.json\' extension. must be in \'./data/raw\'.')
    args = parser.parse_args()

    # Load the dataset
    filepath = f'./data/raw/{args.filename}.json'
    with open(filepath, 'r') as file:
        data = json.load(file)

    # Apply the corrections
    for correction in corrections:
        xw_id = correction['xw']
        entry_id = correction['entry']
        entry = get_entry(data, xw_id, entry_id)
        if entry:
            for key, val in correction.items():
                if key not in ['xw', 'entry']:
                    entry[key] = val

    # Quick check to make sure the code above has done what we expect
    entry = get_entry(data, xw_id='10252', entry_id='19-down')
    assert (entry is None) or (entry['clue'] == 'Ponder (5)')
    
    # Remove the crosswords we're not interested in
    for xw_id in broken_xws:
        data.pop(xw_id, None)
    
    # Save the updated dataset
    with open(filepath, 'w') as file:
        json.dump(data, file)
