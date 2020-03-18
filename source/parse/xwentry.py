import re
from warnings import warn


def read_clue(text):
    def not_blank(s): return s != ""
    
    # check type of clue
    match1 = re.match(r'^(.+)\([\d\-,; ]+\)$', text)
    match2 = re.match(
        r'^[S|s]ee (\d+(?: (?:across|down))?(?:, )?)+(?: \([\d\-,; ]+\))?[ ]*$', text)

    # case 1: standard clue (e.g. "Dog (5)")
    if match1 and not match2:
        text = match1.group(1)
        subclues = text.split(' - ')  # split by dashes
        # check type of each subclue
        all_synonyms = []
        anagram = None
        for subclue in subclues:
            match = re.match(r'.*\(anag\).*', subclue)
            # case 1: synonym
            if match is None:
                synonym_text = subclue
                synonym_text = re.sub(r'\([b|d]\. \d+\)',     # hardcoded rule: remove anything like "(b. 1650)" or "(d. 1773)"
                                      '', synonym_text)
                synonym_text = re.sub(r'\(\d+-\d+\)',         # hardcoded rule: remove date ranges like "(1743-1789)"
                                      '', synonym_text)
                synonym_text = re.sub(r'''[^a-zA-Z'\- ]''',   # remove punctuation we're not interested in
                                      '', synonym_text)
                synonym_text = synonym_text.lower()           # convert to lowercase
                # split by spaces and hyphens
                synonyms = list(re.findall(r"[^ -]+", synonym_text))    
                # synonyms = [re.sub(r"^-+", '', token)          # remove "-" from start of all words
                #            for token in synonym]
                # synonyms = [re.sub(r"-+$", '', token)          # remove "-" from end of all words
                #            for token in synonym]
                synonyms = [re.sub(r"'s$", '', token)          # remove "'s" from end of all words
                           for token in synonyms]
                synonyms = [re.sub(r"^'+", '', token)          # remove all other apostrophes from beginning of words
                           for token in synonyms]
                synonyms = [re.sub(r"'+$", '', token)          # remove all other apostrophes from end of words
                           for token in synonyms]
                # synonyms = [token.replace('-', '_')            # replace hyphens "-" with underscores "_"
                #            for token in synonyms]
                synonyms = list(filter(not_blank, synonyms))    # remove blank entries
                all_synonyms.append(synonyms)
            # case 2: anagram
            else:
                # it's an error if there is already an anagram for this clue
                if anagram:
                    raise ValueError(f'Multiple anagrams in one clue ("{text}")')
                
                anagram_text = re.sub(r'\(anag\)',            # remove string "(anag)"
                                      '', subclue)
                anagram_text = re.sub(r'[^a-zA-Z]',           # remove non-letter characters
                                      '', anagram_text)
                anagram = anagram_text.lower()                # convert to lowercase

    # case 2: reference to another entry (e.g. "See 8 across")
    elif match2:
        all_synonyms = None
        anagram = None

    # otherwise: failed to understand clue, hence error
    else:
        err = f'Could not parse clue, "{text}"'
        raise ValueError(err)

    return all_synonyms, anagram


class CrosswordEntry:
    def __init__(self, id, solution, tiles_spanned=None, separators=[],
                 clue_text="", synonyms=None, anagram=None):
        """A single entry in a crossword puzzle.

        Typically corresponds to one row or column. However an entry can also span
        multiple rows or columns, especially for multiword answers. This is
        represented by the 'tiles_spanned' attribute.

        Args:
            id: string with this entry's ID. mostly used for diagnostics.
            solution: string with answer word(s)
            tiles_spanned: list of positions (x,y) in the crossword grid where this
                entry appears.
            separators: list of (index, char) pairs. Refers to places where the
                solution breaks into separate tokens, e.g. solution = 'FULLOFBEANS',
                separators = [(4, ' '), (6, ' ')].
            synonyms: a list of lists of strings, could be empty.
                example - [['kitchen', 'surface'], ['game', 'token']]
                for solution 'COUNTER'.
            anagram: either None or a string.
        """
        # if anagram and not isanagram(solution, anagram):
        #   err = f"Solution ('{solution}') does not match anagram ('{anagram}') in entry '{id}'"
        #   raise ValueError(err)
        self.id = id
        self.solution = solution
        self.tiles_spanned = tiles_spanned
        self.separators = sorted(separators)
        self.clue_text = clue_text
        self.synonyms = synonyms
        self.anagram = anagram
        self._tokens = None
        self._token_lengths = None

    @classmethod
    def from_dict(cls, d: dict, xw_id = None):
        """Make a crossword entry from the dictionary.

        Args:
            d: Should be the same format as returned by the Guardian's API
                for a single entry.
            xw_id: ID of the crossword this entry belongs to. Not used for
                anything apart from diagnostics, defaults to 'None'.
        """
        entry_id = d['id']
        solution = d['solution'].lower()
        # work out where this entry sits on the board
        length = d['length']
        direction = d['direction']
        x = d['position']['x']
        y = d['position']['y']
        tiles_spanned = []
        for i in range(length):
            if direction == 'across':
                tiles_spanned.append((x+i, y))
            elif direction == 'down':
                tiles_spanned.append((x, y+i))
            else:
                err = f'Unrecognised direction ("{direction}") for entry "{entry_id}"'
                raise ValueError(err)
        # work out where the separators go
        separators = []
        for sep, pos in d['separatorLocations'].items():
            if sep == ',':
                sep = ' '  # replace commas with spaces
            if sep == ';':
                sep = ' '  # replace semicolons with spaces
            for index in pos:
                separators.append((index, sep))
        # parse the clue text
        clue_text = d['clue']
        try:
            synonyms, anagram = read_clue(clue_text)
        except ValueError as err:
            msg = f'Unable to parse clue ("{clue_text}") for entry "{entry_id}"'
            if xw_id:
                msg += f' of crossword "{xw_id}"'
            warn(msg)
            synonyms, anagram = None, None
        # done!
        return cls(entry_id, solution, tiles_spanned, separators,
                   clue_text, synonyms, anagram)

    @property
    def solution_length(self):
        """Length of the solution, in characters. Excludes separators (spaces, dashes, etc.)"""
        return len(self.solution)

    @property
    def pretty_solution(self):
        """Solution with separators added (spaces, dashes, etc.)"""
        text = self.solution
        for i, (index, char) in enumerate(self.separators):
            text = text[:i+index] + char + text[i+index:]
        return text

    @property
    def pretty_length(self):
        """Length of solution including separators."""
        return len(self.solution) + len(self.separators)

    @property
    def underscored_solution(self):
        """Solution with underscores between tokens."""
        text = self.solution
        for i, (index, _) in enumerate(self.separators):
            text = text[:i+index] + '_' + text[i+index:]
        return text

    @property
    def tokenized_solution(self):
        """Individual tokens in the solution."""
        separators1 = [(0, None)] + self.separators
        separators2 = self.separators + [(self.solution_length, None)]
        tokens = []
        for (index1, _), (index2, _) in zip(separators1, separators2):
            tokens.append(self.solution[index1:index2])
        return tokens

    @property
    def token_lengths(self):
        """Lengths of tokens in solutions."""
        if self._token_lengths is None:
            self._token_lengths = [len(token)
                                   for token in self.tokenized_solution]
        return self._token_lengths

    @property
    def all_synonyms(self):
        """All the synonyms in one long list."""
        if self.synonyms:
            return [token for l in self.synonyms for token in l]
        else:
            return None
