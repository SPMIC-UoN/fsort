"""
FSORT: Base class for a module which identifies and copies files for a particular purpose
"""
import logging
import os
import shutil

import nibabel as nib

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
        self._scale_factor, self._scale_inverse = None, None
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
            LOG.debug(f" - Match: checking {file.fname_nodir}")
            if file.matches(match_type=match_type, **kwargs):
                LOG.debug(f" - Matched {file.fname_nodir}")
                matches.append(file)
        return matches

    def add(self, match_type=CONTAINS, **kwargs):
        """
        Add files
        """
        for file in self._match(match_type, **kwargs):
            if file not in self._selected:
                LOG.debug(f" - Add: {file.fname_nodir}")
                self._selected.append(file)

    def count(self, match_type=CONTAINS, **kwargs):
        """
        Count matching selected files
        """
        return len(self._match(candidates=self._selected, match_type=match_type, **kwargs))
    
    def remove(self, match_type=CONTAINS, reason=None, **kwargs):
        """
        Remove files previously added
        """
        for file in self._match(match_type, **kwargs):
            if file in self._selected:
                if reason:
                    LOG.info(f" - Removing {file.fname_nodir}: {reason}")
                else:
                    LOG.debug(f" - Removing: {file.fname_nodir}")
                self._selected.remove(file)

    def filter(self, match_type=CONTAINS, reason=None, **kwargs):
        """
        Keep only files matching new criteria
        """
        matches = self._match(candidates=self._selected, match_type=match_type, **kwargs)
        for file in list(self._selected):
            if file not in matches:
                if reason:
                    LOG.info(f" - Filtering {file.fname_nodir}: {reason}")
                else:
                    LOG.debug(f" - Filtering: {file.fname_nodir}")
                self._selected.remove(file)

    def scale(self, factor, inverse=False):
        """
        Scale data by given factor
        """
        if self._scale_factor is not None:
            LOG.warn(" - Scaling factor already defined - overriding")

        self._scale_factor, self._scale_inverse = factor, inverse

    def group(self, *attrs):
        """
        Group files based on one or more attributes
        """
        self._groups = {}
        for f in self._selected:
            key = tuple([getattr(f, attr) for attr in attrs])
            if key not in self._groups:
                self._groups[key] = []
            LOG.debug(f" - Adding file {f.fname_nodir} to group {key}")
            self._groups[key].append(f)
        LOG.info(f" - Grouping by {attrs}: {len(self._groups)} groups found")

    def select_latest(self, warn=True):
        self._selected = []
        new_groups = {}
        for key, files in self._groups.items():
            if len(files) == 0:
                new_groups[key] = []
            else:
                LOG.debug(f" - Selecting latest of {len(files)} files for key {key}")
                latest, timestamp = self._latest_file(files)
                LOG.debug(f" - {latest}, acquisition time {timestamp}")
                new_groups[key] = [latest]
                if len(files) > 1 and warn:
                    LOG.warn(f" - Select latest file - discarding {len(files)-1} files for group {key}")
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

    def _get_scale_factor(self, f):
        if isinstance(self._scale_factor, str):
            factor = getattr(f, self._scale_factor)
            LOG.info(f" - Scaling {f.fname_nodir} using attribute {self._scale_factor} ({factor})")
            factor = float(factor)
        else:
            factor = float(self._scale_factor)
        if self._scale_inverse:
            factor = 1.0/factor
        LOG.info(f" - Scaling {f.fname_nodir} by factor {factor}")
        return factor

    def save(self, prefix, vol=None, symlink=False, match_type=CONTAINS, **matchers):
        if symlink and (self._factor is not None or vol is not None):
            raise RuntimeError("Cannot symlink output files when scaling and/or volume selection is being used")

        num_matches = self.count(match_type, **matchers)
        n = 1
        for file in self._selected:
            if file.matches(match_type=match_type, **matchers):
                if num_matches > 1:
                    fname = os.path.join(self._outdir, f"{prefix}_{n}.nii.gz")
                    json_fname = os.path.join(self._outdir, f"{prefix}_{n}.json")
                else:
                    fname = os.path.join(self._outdir, f"{prefix}.nii.gz")
                    json_fname = os.path.join(self._outdir, f"{prefix}.json")
                LOG.info(f" - Saving data from {file.fname_nodir} to {fname}")
                if symlink:
                    os.symlink(file.fname, fname)
                    os.symlink(file.json_fname, json_fname)
                else:
                    nii = nib.load(file.fname)
                    fdata = nii.get_fdata()
                    if fdata.ndim > 3 and vol is not None:
                        if vol >= fdata.shape[-1]:
                            raise ValueError(f"Attempting to select volume {vol} but data from {file.fname_nodir} only has {fdata.shape[-1]} volumes")
                        fdata = fdata[..., vol]
                    if self._scale_factor is not None:
                        fdata *= self._get_scale_factor(file)
                    niiout = nib.Nifti1Image(fdata, nii.header.get_best_affine(), nii.header)
                    niiout.to_filename(fname)
                    shutil.copyfile(file.json_fname, json_fname)

                n += 1
