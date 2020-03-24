import re
from warnings import warn


def parse_anagram(text):
    # convert to lowercase
    text = text.lower()
    # remove non-letter characters
    text = re.sub(r'[^a-zA-Z]', '', text)
    return text


def parse_synonym(text):
    # convert to lowercase
    text = text.lower()
    # hardcoded rule: remove anything like "(b. 1650)" or "(d. 1773)"
    text = re.sub(r'\([b|d]\.?\s+\d+\)', '', text)
    # hardcoded rule: remove date ranges like "(1743-1789)"
    text = re.sub(r'\(\d+\-\d+\)', '', text)
    # remove all pairs of brackets
    text = re.sub(r'\(([^\)]+)\)', r'\1', text)
    # remove punctuation we're not interested in
    text = re.sub(r'''[^a-zA-Z'\- ]''', '', text)
    # split by spaces and hyphens
    synonyms = re.split(r'[ \-]+', text)
    # # remove "-" from start of all tokens
    # synonyms = [re.sub(r"^-+", '', token) for token in synonym]
    # # remove "-" from end of all tokens
    # synonyms = [re.sub(r"-+$", '', token) for token in synonym]
    # remove "'s" from end of all tokens
    synonyms = [re.sub(r"'s$", '', token) for token in synonyms]
    # remove all other apostrophes from beginning of tokens
    synonyms = [re.sub(r"^'+", '', token) for token in synonyms]
    # remove all other apostrophes from end of tokens
    synonyms = [re.sub(r"'+$", '', token) for token in synonyms]
    # replace hyphens "-" with underscores "_"
    synonyms = [token.replace('-', '_') for token in synonyms]
    # # remove blank entries
    # synonyms = list(filter(lambda x: x != "", synonyms))
    return synonyms


def parse_subclue(text):
    # normal_match = re.search(r'[a-zA-Z\d\s\-_,;\"\'\.\?\!\(\)]+', text)
    
    # Check category of clue
    anag_match = re.search(r'^(.*)\(anag\.?\)$', text)
    ref_match = re.search(r'^[S|s]ee(?:\s+(?:\d+|and|across|down),?)+$', text)
    syn_match = re.search(r'(.*[a-zA-Z]+.*)', text)
    
    # Choose how to proceed based on category
    if anag_match:
        return "anagram", parse_anagram(anag_match.group(1))
    elif ref_match:
        return "reference", None
    elif syn_match:
        return "synonym", parse_synonym(syn_match.group(1))
    else:
        return "unknown", None


def parse_clue(text):
    # drop length indicators (e.g. drop "(8)" in "Moon shape (8)")
    text = re.sub(r'(\([\d \-,;\.]+\))?\s*$', '', text)

    # drop spaces from start and end of string
    text = re.sub(r'^\s+', '', text)
    text = re.sub(r'\s+$', '', text)
    
    # split into subclues, separated by dashes
    subclues = re.split(r'\s+\-\s+', text)
    
    # parse each subclue, and return list of results
    return [parse_subclue(text) for text in subclues]


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
        # Keep track of warning messages for diagnostics
        warnings = []
        
        entry_id = d['id']
        
        solution = d['solution'].lower()
        solution = re.sub(r'[^a-z]', '', solution)
        if len(solution) == 0:
            warnings.append(f'Blank solution')
        
        # Work out where this entry sits on the board
        length = d['length']
        direction = d['direction']
        x = d['position']['x']
        y = d['position']['y']
        
        tiles_spanned = []
        if direction == 'across':
            for i in range(length):
                tiles_spanned.append((x+i, y))
        elif direction == 'down':
            for i in range(length):
                tiles_spanned.append((x, y+i))
        else:
            warnings.append(f'Unrecognised direction ("{direction}")')
        
        # Work out where the separators go
        separators = []
        
        for sep, pos in d['separatorLocations'].items():
            if sep == ',':
                sep = ' '  # replace commas with spaces
            elif sep == ';':
                sep = ' '  # replace semicolons with spaces
            
            for index in pos:
                separators.append((index, sep))
        
        # Parse the clue text
        clue_text = d['clue']
        clues = parse_clue(clue_text)
        
        synonyms = [val for category, val in clues if category == 'synonym']
        anagrams = [val for category, val in clues if category == 'anagram']
        references = [val for category, val in clues if category == 'reference']
        unknowns = [val for category, val in clues if category == 'unknown']
        
        if len(synonyms) == 0:
            synonyms = None
        
        if len(anagrams) > 0:
            anagram = anagrams[0]
            if len(anagrams) > 1:
                warnings.append(f'Multiple anagrams in one clue ("{clue_text}")')
        else:
            anagram = None
        
        if len(unknowns) > 0:
            warnings.append(f'Unable to parse clue ("{clue_text}")')
        
        for warning in warnings:
            warning += f' for entry "{entry_id}"'
            if xw_id:
                warning += f' of crossword "{xw_id}"'
            warn(warning)
        
        # Return result
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
