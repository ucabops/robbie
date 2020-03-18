from xwentry import CrosswordEntry
from xwpuzzle import Crossword


class CrosswordSet:
    def __init__(self, crosswords):
        self.crosswords = crosswords
        self._entries = None

    @classmethod
    def from_dict(cls, data):
        return CrosswordSet({xw_id: Crossword(xw_dict)
                             for xw_id, xw_dict in data.items()})

    def __len__(self):
        return len(self.crosswords)

    def __iter__(self):
        return iter(self.crosswords.items())

    def __getitem__(self, id):
        """The crossword with the given id.

        e.g. 'xw = xwset[12000]' for Guardian quick crossword no. 12000
        """
        return self.crosswords[id]

    @property
    def crosswords_as_list(self):
        """All the crosswords as one long list."""
        return self.crosswords.values()

    @property
    def entries(self):
        """All the crossword entries as one long list."""
        if self._entries is None:
            self._entries = [xw.entries for xw in self.crosswords]
        return self._entries
