"""
FSORT: Identifying and copying files for a particular purpose
"""
import logging
import os

import numpy as np

LOG = logging.getLogger(__name__)

class Sorter:
    """
    Base class for object which identifies and copies files for a particular purpose
    """

    # Matching modes
    EXACT = "exact"
    CONTAINS = "contains"
    REGEX = "regex"
    GLOB = "glob"

    def __init__(self, name):
        """
        :param name: Unique name for this sorter within a given configuration file
        """
        self.name = name
        self._outdir = None
        self._scale_attribute, self._scale_factor, self._scale_inverse = None, None, None
        self.clear_selection()
        self._candidates = []

    def clear_selection(self):
        """
        Clear currently selected files
        """
        self.selected = []
        self.groups = {}

    @property
    def candidates(self):
        return self._candidates
    
    @candidates.setter
    def candidates(self, files):
        self._candidates = files
        self.clear_selection()

    @property
    def outdir(self):
        return self._outdir
    
    @outdir.setter
    def outdir(self, outdir):
        self._outdir = outdir
        with open(self.manifest_fname, "w") as mf:
            mf.write("source\tdestination\tvolume\tscale_factor\tscale_const\tscale_attribute\tscale_inverse\n")

    @property
    def manifest_fname(self):
        return os.path.join(self._outdir, "manifest.txt")

    def process_files(self, files, vendor, outdir):
        """
        Process a set of candidate files
        
        :param files: Sequence of ImageFile objects
        :param vendor: Vendor name
        :param outdir: Output directory to write files for
        """
        self.candidates = files
        self.outdir = outdir
        if hasattr(self, f"run_{vendor}"):
            getattr(self, f"run_{vendor}")()
        else:
            self.run()

    def run(self):
        """
        This method must be implemented by the subclass to perform required matching operations
        """
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

    def add(self, match_type=CONTAINS, expected_number=None, **kwargs):
        """
        Add files to the selected list

        :param match_type: Matching type
        :param expected_number: Optional expected number of matching files - will not add unless this number found
        :param kwargs: key/value attribute pairs for matching
        """
        to_add = []
        for file in self._match(match_type, **kwargs):
            if file not in self.selected:
                LOG.debug(f" - Add: {file.fname}")
                to_add.append(file)

        num_found = len(to_add)
        if expected_number is None:
            allowed = True
        else:
            allowed = any([num_found == num for num in np.atleast_1d(expected_number)])

        if num_found > 0 and not allowed:
            LOG.warn(f" - Expected {expected_number} files, found {len(to_add)} - not adding")
            return 0
        else:
            self.selected.extend(to_add)
            return num_found

    def count(self, match_type=CONTAINS, count_candidates=False, **kwargs):
        """
        Count matching selected files
        """
        return len(self._match(candidates=self.selected if not count_candidates else None, match_type=match_type, **kwargs))
    
    def remove(self, match_type=CONTAINS, reason=None, **kwargs):
        """
        Remove files previously added
        """
        for file in self._match(match_type, **kwargs):
            if file in self.selected:
                if reason:
                    LOG.info(f" - Removing {file.fname}: {reason}")
                else:
                    LOG.debug(f" - Removing: {file.fname}")
                self.selected.remove(file)

    def filter(self, match_type=CONTAINS, reason=None, **kwargs):
        """
        Keep only files matching new criteria
        """
        matches = self._match(candidates=self.selected, match_type=match_type, **kwargs)
        for file in list(self.selected):
            if file not in matches:
                if reason:
                    LOG.info(f" - Filtering {file.fname}: {reason}")
                else:
                    LOG.debug(f" - Filtering: {file.fname}")
                self.selected.remove(file)

    def scale(self, factor=1.0, attribute=None, inverse=False):
        """
        Scale data by given factor
        """
        if self._scale_factor is not None:
            LOG.warn(" - Scaling factor already defined - overriding")

        self._scale_factor, self._scale_attribute, self._scale_inverse = factor, attribute, inverse

    def group(self, *attrs, **kwargs):
        """
        Group files based on one or more attributes
        """
        allow_none = kwargs.get("allow_none", True)
        self.groups = {}
        for f in self.selected:
            key = tuple([getattr(f, attr) for attr in attrs])
            if None in key and not allow_none:
                LOG.warn(f" - Group: ignoring file {f.fname}, {key} contains None values")
                continue

            if key not in self.groups:
                self.groups[key] = []
            LOG.debug(f" - Adding file {f.fname} to group {key}")
            self.groups[key].append(f)
        LOG.info(f" - Grouping by {attrs}: {len(self.groups)} groups found")

    def select_latest(self, warn=True):
        if not self.groups:
            self.groups = {None : self.selected}
        self.selected = []
        new_groups = {}
        for key, files in self.groups.items():
            if len(files) == 0:
                new_groups[key] = []
            else:
                LOG.debug(f" - Selecting latest of {len(files)} files for key {key}")
                latest, timestamp = self._latest_file(files)
                LOG.debug(f" - {latest}, acquisition time {timestamp}")
                new_groups[key] = [latest]
                if len(files) > 1 and warn:
                    discarded = [f.fname for f in files if f != latest]
                    LOG.warn(f" - Select latest file - keeping {latest.fname} and discarding {len(files)-1} files for group {key}: {discarded}")
                self.selected.append(latest)

    def _latest_file(self, files):
        latest_file, latest_timestamp = None, None
        for f in files:
            if latest_timestamp is None or f.acquisitiontime > latest_timestamp:
                latest_timestamp = f.acquisitiontime
                latest_file = f
        return latest_file, latest_timestamp

    def have_files(self):
        return len(self.selected) > 0

    def _get_scale_factor(self, f):
        overall_factor = 1.0
        if self._scale_attribute:
            factor = getattr(f, self._scale_attribute)
            if self._scale_inverse:
                factor = 1.0/factor
            LOG.info(f" - Scaling {f.fname} using attribute {self._scale_attribute}, inverse={self._scale_inverse} ({factor})")
            overall_factor *= float(factor)
        if self._scale_factor is not None:
            overall_factor *= float(self._scale_factor)
            LOG.info(f" - Scaling {f.fname} by factor {self._scale_factor}")
        if overall_factor == 1.0:
            LOG.info(f" - Overall scaling of {f.fname} by factor {overall_factor}")
        return overall_factor

    def save(self, prefix, vol=None, symlink=False, match_type=CONTAINS, sort=None, **matchers):
        if symlink and (self._scale_factor is not None or vol is not None):
            raise RuntimeError("Cannot symlink output files when scaling and/or volume selection is being used")

        manifest = []
        num_matches = self.count(match_type, **matchers)
        LOG.debug(f" - Unsorted files: {self.selected}")
        n = 1
        if sort is not None:
            sorted_files = sorted(self.selected, key=lambda x: getattr(x, sort) if getattr(x, sort) is not None else 0)
        else:
            sorted_files = self.selected
        LOG.debug(f" - Sorted files: {sorted_files} {self.selected}")
        for file in sorted_files:
            if file.matches(match_type=match_type, **matchers):
                if num_matches > 1:
                    fname = f"{prefix}_{n}.nii.gz"
                    json_fname = f"{prefix}_{n}.json"
                else:
                    fname = f"{prefix}.nii.gz"
                    json_fname = f"{prefix}.json"
                fpath = os.path.join(self._outdir, fname)
                json_fpath = os.path.join(self._outdir, json_fname)
                LOG.info(f" - Saving data from {file.fname} to {fname}")
                sf = None
                if symlink:
                    os.symlink(file.fpath, fpath)
                    os.symlink(file.json_fpath, json_fpath)
                else:
                    fdata = file.data
                    if fdata.ndim > 3 and vol is not None:
                        if isinstance(vol, int):
                            vol = [vol]
                        if max(vol) >= fdata.shape[-1]:
                            raise ValueError(f"Attempting to select volume {vol} but data from {file.fname} only has {fdata.shape[-1]} volumes")
                        fdata_new = np.zeros(list(fdata.shape[:3]) + [len(vol)], dtype=fdata.dtype)
                        for idx, v in enumerate(vol):
                            fdata_new[..., idx] = fdata[..., v]
                        fdata = fdata_new
                    if self._scale_factor is not None:
                        sf = self._get_scale_factor(file)
                        fdata = sf*fdata
                    file.save_derived(fdata, fpath)
                manifest.append((file.fname, fname, vol, sf, self._scale_factor, self._scale_attribute, self._scale_inverse))
                n += 1

        with open(self.manifest_fname, "a") as mf:
            for line in manifest:
                mf.write("\t".join([str(v) for v in line]) + "\n")
