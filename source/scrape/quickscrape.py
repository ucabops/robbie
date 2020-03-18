import argparse
import json
import urllib.request

from bs4 import BeautifulSoup


def scrape(xw):
    url = f'https://www.theguardian.com/crosswords/quick/{xw}'
    with urllib.request.urlopen(url) as response:
        html = response.read()
        soup = BeautifulSoup(html, features='html.parser')
        data = soup.find('div', class_='js-crossword')['data-crossword-data']
        return json.loads(data)


if __name__ == '__main__':
    script_desc = 'Download quick crosswords from the Guardian\'s website.'
    parser = argparse.ArgumentParser(description=script_desc)
    parser.add_argument('first', type=int,
                        help='first crossword to download')
    parser.add_argument('last', type=int,
                        help='last crossword to download')
    args = parser.parse_args()
    
    # Specify range of crosswords to download
    xw_range = range(args.first, args.last + 1)
    num_xws = len(xw_range)

    # Scrape data
    xwset = {}
    for i, xw in enumerate(xw_range, start=1):
        print(f'Downloading crossword {i} of {num_xws} (#{xw})...')
        xwset[str(xw)] = scrape(xw)
    
    # Save results
    out_path = f'./data/raw/gquick-{num_xws}.json'
    with open(out_path, 'w+') as file:
        json.dump(xwset, file)
    
    print(f"Dataset saved to {out_path}")
