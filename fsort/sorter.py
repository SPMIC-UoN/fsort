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
        self._scale_attribute, self._scale_factor, self._scale_inverse = None, None, None
        self.clear_selection()
        self._candidates = []
        self._manifest_fname = None

    def clear_selection(self):
        self._selected = []
        self._groups = {None : self._selected}

    def process_files(self, files, vendor, outdir):
        self.clear_selection()
        self._candidates = files
        self._outdir = outdir
        self._manifest_fname = os.path.join(self._outdir, "manifest.txt")
        with open(self._manifest_fname, "w") as mf:
            mf.write("source\tdestination\tvolume\tscale_factor\tscale_const\tscale_attribute\tscale_inverse\n")
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
    
    def remove(self, match_type=CONTAINS, reason=None, **kwargs):
        """
        Remove files previously added
        """
        for file in self._match(match_type, **kwargs):
            if file in self._selected:
                if reason:
                    LOG.info(f" - Removing {file.fname}: {reason}")
                else:
                    LOG.debug(f" - Removing: {file.fname}")
                self._selected.remove(file)

    def filter(self, match_type=CONTAINS, reason=None, **kwargs):
        """
        Keep only files matching new criteria
        """
        matches = self._match(candidates=self._selected, match_type=match_type, **kwargs)
        for file in list(self._selected):
            if file not in matches:
                if reason:
                    LOG.info(f" - Filtering {file.fname}: {reason}")
                else:
                    LOG.debug(f" - Filtering: {file.fname}")
                self._selected.remove(file)

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
        self._groups = {}
        for f in self._selected:
            key = tuple([getattr(f, attr) for attr in attrs])
            if None in key and not allow_none:
                LOG.warn(f" - Group: ignoring file {f.fname}, {key} contains None values")
                continue

            if key not in self._groups:
                self._groups[key] = []
            LOG.debug(f" - Adding file {f.fname} to group {key}")
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
                    discarded = [f.fname for f in files if f != latest]
                    LOG.warn(f" - Select latest file - keeping {latest.fname} and discarding {len(files)-1} files for group {key}: {discarded}")
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

    def save(self, prefix, vol=None, symlink=False, match_type=CONTAINS, **matchers):
        if symlink and (self._factor is not None or vol is not None):
            raise RuntimeError("Cannot symlink output files when scaling and/or volume selection is being used")

        manifest = []
        num_matches = self.count(match_type, **matchers)
        n = 1
        for file in self._selected:
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
                        if vol >= fdata.shape[-1]:
                            raise ValueError(f"Attempting to select volume {vol} but data from {file.fname} only has {fdata.shape[-1]} volumes")
                        fdata = fdata[..., vol]
                    if self._scale_factor is not None:
                        sf = self._get_scale_factor(file)
                        fdata *= sf
                    file.save_derived(fdata, fpath)
                manifest.append((file.fname, fname, vol, sf, self._scale_factor, self._scale_attribute, self._scale_inverse))
                n += 1

        with open(self._manifest_fname, "a") as mf:
            for line in manifest:
                mf.write("\t".join([str(v) for v in line]) + "\n")
