"""
FSORT: Class providing useful file sorting functions
"""
import logging
import os

LOG = logging.getLogger(__name__)

class Sorter:

    # Matching modes
    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    GLOB = "glob"

    def __init__(self, name):
        self.name = name
        self._outdir = None
        self.clear_selection()

    def clear_selection(self):
        self._selected = []
        self._candidates = []
        self._groups = {None : self._selected}

    def process_files(self, files, vendor, outdir):
        self.clear_selection()
        self._candidates = files
        self._outdir = outdir
        if hasattr(self, f"run_{vendor}"):
            getattr(self, f"run_{vendor}")()
        else:
            self.run()

    def run(self):
        raise NotImplementedError(f"run() has not been implemented for sorter {self.name}")

    def _match(self, match_type=CONTAINS, candidates=None, **kwargs):
        matches = []
        if candidates is None:
            candidates = self._candidates
        for file in candidates:
            LOG.debug(f" - Match: checking {file.fname}")
            if file.matches(match_type=match_type, **kwargs):
                LOG.debug(f" - Matched {file.fname}")
                matches.append(file)
        return matches

    def add(self, match_type=CONTAINS, **kwargs):
        """
        Add files
        """
        for file in self._match(match_type, **kwargs):
            if file not in self._selected:
                LOG.debug(f" - Add: {file.fname}")
                self._selected.append(file)

    def count(self, match_type=CONTAINS, **kwargs):
        """
        Count matching selected files
        """
        return len(self._match(candidates=self._selected, match_type=match_type, **kwargs))
    
    def remove(self, match_type=CONTAINS, **kwargs):
        """
        Remove files previously added
        """
        for file in self._match(match_type, **kwargs):
            if file in self._selected:
                LOG.debug(f" - Remove: {file.fname}")
                self._selected.remove(file)

    def filter(self, match_type=CONTAINS, **kwargs):
        """
        Keep only files matching new criteria
        """
        matches = self._match(candidates=self._selected, match_type=match_type, **kwargs)
        for file in list(self._selected):
            if file not in matches:
                LOG.debug(f" - Filter: {file.fname}")
                self._selected.remove(file)

    def scale(self, factor, inverse=False):
        """
        Scale data by given factor
        """
        LOG.warn(" - Scaling not yet implemented")
        #raise NotImplementedError()
    
    def select_vol(self, vol_idx):
        """
        Select given volume index
        """
        raise NotImplementedError()

    def group(self, *attrs):
        """
        Group files based on one or more attributes
        """
        self._groups = {}
        for f in self._selected:
            key = tuple([getattr(f, attr) for attr in attrs])
            if key not in self._groups:
                self._groups[key] = []
            LOG.debug(f" - Adding file {f.fname} to group {key}")
            self._groups[key].append(f)
        LOG.info(f" - Grouping by {attrs}: {len(self._groups)} groups found")

    def select_latest(self):
        self._selected = []
        new_groups = {}
        for key, files in self._groups.items():
            LOG.debug(f" - Selecting latest of {len(files)} files for key {key}")
            latest, timestamp = self._latest_file(files)
            LOG.debug(f" - {latest}, acquisition time {timestamp}")
            new_groups[key] = [latest]
            self._selected.append(latest)
    
    def _latest_file(self, files):
        latest_file, latest_timestamp = None, None
        for f in files:
            if latest_timestamp is None or f.acquisitiontime > latest_timestamp:
                latest_timestamp = f.acquisitiontime
                latest_file = f
        return latest_file, latest_timestamp

    def have_files(self):
        return len(self._selected) > 0

    def save(self, prefix, match_type=CONTAINS, **matchers):
        n = 1
        for file in self._selected:
            if file.matches(match_type=match_type, **matchers):
                fname = os.path.join(self._outdir, f"{prefix}_{n}.nii.gz")
                LOG.info(f" - Saving selected file to {fname}")
                os.symlink(file.fname, fname)
                n += 1
