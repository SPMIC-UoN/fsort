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

    def __init__(self, name, **kwargs):
        """
        :param name: Unique name for this sorter within a given configuration file
        """
        self.name = name
        self._outdir = None
        self.clear_selection()
        self._candidates = []
        self._candidate_sets = {}
        self._using_set = 0
        self.kwargs = kwargs

    def clear_selection(self):
        """
        Clear currently selected files
        """
        self.selected = []
        self.groups = {}
        self._scale_attribute, self._scale_factor, self._scale_inverse = None, None, None

    @property
    def candidates(self):
        return self._candidates
    
    @candidates.setter
    def candidates(self, files):
        self._candidates = files
        self.clear_selection()

    @property
    def candidate_set(self):
        return self._using_set

    @candidate_set.setter
    def candidate_set(self, set_id):
        if set_id not in self._candidate_sets:
            raise RuntimeError(f"Candidate set not found: {set_id}")
        LOG.info(f" - Selecting conversion source set {set_id}")
        self._using_set = set_id
        self.candidates = self._candidate_sets[set_id]

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

    def process_files(self, file_sets, vendor, outdir):
        """
        Process a set of candidate files
        
        :param files: Sequence of ImageFile objects
        :param vendor: Vendor name
        :param outdir: Output directory to write files for
        """
        self._candidate_sets = file_sets
        self.outdir = outdir
        self.candidate_set = self.kwargs.get("default_candidate_set", 0)
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
            # Existing groups are invalidated when we add files
            self.groups = {}
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
                # Existing groups are invalidated when we remove files
                self.groups = {}

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
                # Existing groups are invalidated when we add files
                self.groups = {}

    def scale(self, factor=1.0, attribute=None, inverse=False):
        """
        Scale data by given factor
        """
        if self._scale_factor is not None:
            LOG.warn(" - Scaling factor already defined - overriding")
        if not isinstance(inverse, list):
            inverse = [inverse,]
        if not attribute:
            attribute = []
        if not isinstance(attribute, list):
            attribute = [attribute,]
        if len(attribute) > 1 and len(inverse) == 1:
            inverse = inverse * len(attribute)
        if len(attribute) > 0 and len(inverse) > 0 and len(inverse) != len(attribute):
            raise RuntimeError("List of scale attributes and inverse flags must have the same length")
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
        return self.select_one("acquisitiontime", last=True)

    def select_earliest(self, warn=True):
        return self.select_one("acquisitiontime", last=False)

    def select_one(self, attr, last=True, warn=True):
        """
        Select a single file from each group
        
        :param attr: Attribute to use for ordering
        :param last: If True, select last, otherwise select first type-specific ordering
        :param warn: Warn about discarded files
        """
        if not self.groups:
            self.groups = {None : self.selected}
        self.selected = []
        new_groups = {}
        for key, files in self.groups.items():
            if len(files) == 0:
                new_groups[key] = []
            else:
                LOG.debug(f" - Selecting one of {len(files)} files for key {key}")
                selected, value = self._one_file(files, attr, last)
                LOG.debug(f" - {selected}, {attr}={value}")
                if selected is None:
                    selected = files[0]
                    if len(files) > 1:
                        LOG.warn(f" - No valid value found for attribute {attr} in group {key} - selected first in list")
                if len(files) > 1 and warn:
                    discarded = [f.fname for f in files if f != selected]
                    LOG.warn(f" - Select single file - keeping {selected.fname} with {attr}={value} and discarding {len(files)-1} files for group {key}: {discarded}")
                new_groups[key] = [selected]
                self.selected.append(selected)

    def _one_file(self, files, attr, last):
        selected, selected_value = None, None
        for f in files:
            f_value = getattr(f, attr)
            if f_value is None:
                # Ignore files with no value for this attribute
                continue
            if selected_value is None or (last and f_value > selected_value) or (not last and f_value < selected_value):
                selected_value = f_value
                selected = f
        return selected, selected_value

    def have_files(self):
        return len(self.selected) > 0

    def _get_scale_factor(self, f):
        overall_factor = 1.0
        if self._scale_attribute:
            for attr, inverse in zip(self._scale_attribute, self._scale_inverse):
                factor = getattr(f, attr)
                if factor is None:
                    LOG.warn(f" - No attribute {attr} found for scaling - ignoring")
                    continue
                if inverse:
                    factor = 1.0/factor
                LOG.info(f" - Scaling {f.fname} using attribute {attr}, inverse={inverse} ({factor})")
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
                        if len(vol) == 1:
                            fdata = np.squeeze(fdata, axis=3)
                    if self._scale_factor is not None:
                        sf = self._get_scale_factor(file)
                        fdata = sf*fdata
                    file.save_derived(fdata, fpath, copy_bdata=True)
                manifest.append((file.fname, fname, vol, sf, self._scale_factor, self._scale_attribute, self._scale_inverse))
                n += 1

        with open(self.manifest_fname, "a") as mf:
            for line in manifest:
                mf.write("\t".join([str(v) for v in line]) + "\n")
