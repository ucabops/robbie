from itertools import product
from warnings import warn

from xwentry import CrosswordEntry


class Crossword:
    def __init__(self, data):
        """A crossword puzzle.

        Args:
            data: A dictionary containing all info on the crossword. You should use
                the JSON from the Guardian's API, unmodified.
        """
        # get the crossword id. useful for diagnostics, not used for much else.
        xw_id = str(data["number"])
        self._id = xw_id
        # store the entries, indexed by group
        entries_raw = {}
        for entry_dict in data["entries"]:
            entry_id = entry_dict["group"][0]
            entry = CrosswordEntry.from_dict(entry_dict, xw_id)
            entries_for_id = entries_raw.get(entry_id, [])
            entries_for_id.append(entry)
            entries_raw[entry_id] = entries_for_id
        # merge all entries belonging to the same group into a single entry
        entries = {}
        for entry_id, entry_list in entries_raw.items():
            if len(entry_list) < 2:
                entries[entry_id] = entry_list[0]
            else:
                # find the entry with a proper clue, not just the words "See x across".
                # there should only be one (or it's an error).
                non_trivial_entries = list(
                    filter(lambda x: x.synonyms or x.anagram, entry_list))
                trivial_entries = list(
                    filter(lambda x: not (x.synonyms or x.anagram), entry_list))
                if len(non_trivial_entries) > 1:
                    msg = f'Multiple clues in group "{entry_id}" of crossword "{xw_id}"\n' \
                          f'Details: {[e.clue_text for e in non_trivial_entries]}'
                    warn(msg)
                    entry = non_trivial_entries[0]
                elif len(non_trivial_entries) < 1:
                    msg = f'Invalid clue for group "{entry_id}" of crossword "{xw_id}"\n' \
                          f'(Maybe the clue refers to itself, e.g. "See 8 across" for group "8-across"?)'
                    warn(msg)
                    entry = trivial_entries[0]
                else:
                    entry = non_trivial_entries[0]
                # combine the other entries into this one
                for other_entry in trivial_entries:
                    other_separators = [(len(entry.solution) + pos, sep)
                                        for (pos, sep) in other_entry.separators]
                    entry.solution = entry.solution + other_entry.solution
                    entry.tiles_spanned += other_entry.tiles_spanned
                    entry.separators += other_separators
                entries[entry_id] = entry
        self._entries = entries
        # store the grid's dimensions
        rows = data["dimensions"]["rows"]
        cols = data["dimensions"]["cols"]
        self.dimensions = (rows, cols)
        # placeholders for lazily-computed properties (see below)
        self._grid = None
        self._solved_grid = None
        self._intersections = None
    
    # @classmethod
    # def from_dict(cls, data):
    #     pass

    @property
    def entries(self):
        """All the entries in the crossword."""
        return self._entries.items()

    def entry(self, key):
        """The entry for the given key."""
        return self._entries[key]

    # @property
    # def clues(self):
    #   """Clues for all the entries in the crossword."""
    #   return self._clues.items()

    # def clue(self, key):
    #   """Clue for entry with the given key."""
    #   return self._clues[key]

    @property
    def grid(self):
        """Grid mapping positions (x, y) to a list of entries (id, index)."""
        if self._grid is None:
            rows, cols = self.dimensions
            grid = {(x, y): [] for x, y in product(range(cols), range(rows))}
            for entry_id, entry in self.entries:
                for index, (x, y) in enumerate(entry.tiles_spanned):
                    grid[(x, y)].append((entry_id, index))
            self._grid = grid
        return self._grid

    @property
    def solved_grid(self):
        """The solved grid. It's a dict with one letter per (x, y) pair.

        Warning: when a tile is blank, it will NOT exist in the dictionary. To avoid
        key errors, you should ALWAYS access tiles like this:

          xw.solved_grid.get((x, y), None)

        so that a default value of 'None' is returned when the tile is blank.
        """
        if self._solved_grid is None:
            solved_grid = {}
            for pos, l in self.grid.items():
                if len(l) > 0:
                    # get the first tuple, although any will do
                    entry_id, index = l[0]
                    entry = self.entry(entry_id)
                    solved_grid[pos] = entry.solution[index]
            self._solved_grid = solved_grid
        return self._solved_grid

    @property
    def intersections(self):
        """All intersections between entries in the crossword.

        Returns:
            A dict with the structure:
            
                {
                    entry_id_1: [
                        ((entry_id_1, index_1_1), (other_id_1_1, other_index_1_1)),
                        ((entry_id_1, index_1_2), (other_id_1_2, other_index_1_2)),
                        ...],
                    entry_id_2: [
                        ((entry_id_2, index_2_1), (other_id_2_1, other_index_2_1)),
                        ((entry_id_2, index_2_2), (other_id_2_2, other_index_2_2)),
                        ...],
                    entry_id_3: [
                        ((entry_id_3, index_3_1), (other_id_3_1, other_index_3_1)),
                        ((entry_id_3, index_3_2), (other_id_3_2, other_index_3_2)),
                        ...],
                    ...
                }
            
            so that each element of the lists is a pair (entry_id, index) and
            (other_id, other_index), specifying which two entries are in the
            intersection, and which letters in the solution are involved.

        Example:

                xw.entry('5-across').solution = 'GOAT'
                xw.entry('3-down').solution = 'AVACADO'

            Assume there is an intersection (('5-across', 2), ('3-down', 0)), which
            means the third letter of 'GOAT' and the first letter of 'AVACADO' share
            the same tile in the crossword.

            In the dict, this might look like:

                xw.intersections['5-across'] = [
                    (('5-across', 2), ('3-down', 0)),
                    ...]

                xw.intersections['3-down'] = [
                    (('3-down', 0), ('5-across', 2)),
                    ...]

            Note: the information is deliberately repeated twice, to make it easier
            to look up intersections for a specific entry. (In the example above, you
            can use either of '5-across' or '3-down' as the key.)
        """
        if self._intersections is None:
            intersections = {entry_id: [] for (entry_id, _) in self.entries}
            for pos, entries in self.grid.items():
                if len(entries) >= 2:  # only if there are two or more entries on this tile
                    for entry in entries:
                        entry_id, index = entry
                        ls = intersections[entry_id]
                        for other_entry in entries:
                            other_id, other_index = other_entry
                            if entry_id != other_id:
                                ls.append((entry, other_entry))
            self._intersections = intersections
        return self._intersections

    def __str__(self):
        desc = ""
        solved_grid = self.solved_grid
        rows, cols = self.dimensions
        for y in range(rows):
            for x in range(cols):
                pos = (x, y)
                tile = solved_grid.get(pos, None)
                if tile:
                    desc += tile
                    desc += " "
                else:
                    desc += '██'
            # add a newline to go to the next row
            if y + 1 < rows:
                desc += '\n'
        return desc
