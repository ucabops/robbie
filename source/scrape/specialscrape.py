import argparse
import json

from quickscrape import scrape


if __name__ == '__main__':
    script_desc = 'Download a subset of quick crosswords from the Guardian\'s website.'
    parser = argparse.ArgumentParser(description=script_desc)
    args = parser.parse_args()
    
    # Specify list of crosswords to download
    xw_list = [182, 131, 326, 199, 35, 363, 66, 48, 33, 197]
    num_xws = len(xw_list)

    # Scrape data
    xwset = {}
    for i, xw in enumerate(xw_list, start=1):
        xw += 10000
        print(f'Downloading crossword {i} of {num_xws} (#{xw})...')
        xwset[str(xw)] = scrape(xw)
    
    # Save results
    out_path = f'./data/raw/gquick-{num_xws}.json'
    with open(out_path, 'w+') as file:
        json.dump(xwset, file)
    
    print(f"Dataset saved to {out_path}")
