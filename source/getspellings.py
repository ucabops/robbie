import json

from models.amer_brit import wordpairs


if __name__=='__main__':
    d1 = {}
    d2 = {}
    for brit, amer in wordpairs:
        d1[brit] = amer
        d2[amer] = brit
    
    with open('data/brit2amer.json', 'w') as f:
        json.dump(d1, f)

    with open('data/amer2brit.json', 'w') as f:
        json.dump(d2, f)
