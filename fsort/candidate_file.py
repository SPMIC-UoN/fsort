"""
FSORT: Class representing a candidate file
"""
import logging
import math
import os

import numpy as np

LOG = logging.getLogger(__name__)
FLOAT_TOL = 1e-3

class CandidateFile:
    def __init__(self, fname, nii, metadata):
        self.fname = os.path.abspath(os.path.normpath(fname))
        self.fname_nodir = os.path.basename(self.fname)
        self.json_fname = self.fname.replace(".nii.gz", ".json").replace(".nii", ".json")
        self.nii = nii
        self.metadata = metadata

    def __getattr__(self, attr):
        return self.mdval(attr)

    def matches(self, match_type="contains", **kwargs):
        for key, value in kwargs.items():
            myval = getattr(self, key, None)
            LOG.debug(f"Checking for {key} ({myval}) {match_type} {value} in {self.fname}")
            if myval is None:
                match = False
            elif isinstance(myval, float) and isinstance(value, float):
                    match = math.abs(value - myval) < FLOAT_TOL
            elif isinstance(myval, int) and isinstance(value, int):
                    match = value == myval
            elif isinstance(myval, np.ndarray) and isinstance(value, np.ndarray):
                    match = np.allclose(value, myval)
            elif match_type == "contains" and isinstance(myval, (str, list)) and isinstance(value, str):
                match = value.lower() in myval
            elif match_type == "contains" and isinstance(myval, (str, list)) and isinstance(value, list):
                match = any([v.lower() in myval for v in value])
            else:
                raise NotImplementedError(f"Don't know how to test type {type(myval)} {match_type} {type(value)}")

            if not match:
                LOG.debug("No match")
                return False
        LOG.debug("File matched")
        return True

    @property
    def vendor(self):
        return self.mdval("Manufacturer")

    @property
    def shape(self):
        return self.nii.shape

    @property
    def shape3d(self):
        return self.nii.shape[:3]
    
    @property
    def nvols(self):
        if len(self.shape) > 3:
            return self.shape[3]
        else:
            return 1

    @property
    def multivol(self):
        return self.nvols > 1

    @property
    def nslices(self):
        return self.shape[2]

    @property
    def multislice(self):
        return self.nslices > 1
    
    @property
    def affine(self):
        return self.nii.header.get_best_affine()

    def mdval(self, key, default=None, keep_case=False):
        for k in self.metadata:
            if k.lower() == key.lower():
                key = k
        val = self.metadata.get(key, default)
        if isinstance(val, str) and not keep_case:
            val = val.lower()
        if isinstance(val, list) and not keep_case:
            val = [v.lower() for v in val]
        return val
