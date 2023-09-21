"""
FSORT: Class representing a image file
"""
import hashlib
import json
import logging
import math
import os
import shutil

import numpy as np
import nibabel as nib

LOG = logging.getLogger(__name__)
FLOAT_TOL = 1e-3

class ImageFile:
    def __init__(self, fpath, warn_json=False):
        self.fpath = os.path.abspath(os.path.normpath(fpath))
        self.dirname, self.fname = os.path.split(self.fpath)
        self.fname_noext = self.fname[:self.fname.index(".nii")]
        self.json_fpath = self.fpath.replace(".nii.gz", ".json").replace(".nii", ".json")
        self.nii = nib.load(self.fpath)
        self.metadata = {}
        if os.path.exists(self.json_fpath):
            try:
                with open(self.json_fpath) as f:
                    self.metadata = json.load(f)
            except:
                LOG.exception(f"Failed to load JSON sidecar {self.json_fpath} - metadata matching may not work")
        elif warn_json:
            LOG.warn(f"No .JSON metadata for NIFTI file {self.fpath} - metadata matching may not work")

    def save_derived(self, data, fname):
        nii = nib.Nifti1Image(data, self.affine, self.nii.header)
        nii.to_filename(fname)
        if os.path.exists(self.json_fpath):
            new_json_fpath = fname.replace(".nii.gz", ".json").replace(".nii", ".json")
            shutil.copyfile(self.json_fpath, new_json_fpath)

    def save(self, fname):
        if not fname.endswith(".nii") and not fname.endswith(".nii.gz"):
            fname += ".nii.gz"
        self.nii.to_filename(fname)
        if os.path.exists(self.json_fpath):
            new_json_fpath = fname.replace(".nii.gz", ".json").replace(".nii", ".json")
            shutil.copyfile(self.json_fpath, new_json_fpath)

    def __getattr__(self, attr):
        return self.mdval(attr)

    def affine_matches(self, img):
        EQ_TOL = 1e-3
        return np.all(np.abs(self.affine - img.affine) < EQ_TOL)

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
            elif isinstance(myval, list) and isinstance(value, list):
                match = np.allclose(value, myval)
            elif match_type == "contains" and isinstance(myval, str) and isinstance(value, str):
                match = value.lower() in myval.lower()
            elif match_type == "contains" and isinstance(myval, list) and isinstance(value, str):
                match = value.lower() in [v.lower() for v in myval]
            elif match_type == "contains" and isinstance(myval, str) and isinstance(value, list):
                match = any([v.lower() in myval for v in value])
            elif match_type == "contains" and isinstance(myval, list) and isinstance(value, list):
                myval = [v.lower() for v in myval]
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

    @property
    def affinedata(self):
        """
        Data representing the affine designed to be comparable and hashable
        """
        a = self.affine.flatten()
        a = (a*1000).astype(np.int32).tolist()
        return tuple(a)

    @property
    def voxel_volume(self):
        vox_dims = self.nii.header.get_zooms()
        return vox_dims[0]*vox_dims[1]*vox_dims[2] / 1000

    @property
    def data(self):
        data = self.nii.get_fdata()
        while data.ndim < 3:
            data = data[..., np.newaxis]
        return data

    @property
    def hash(self):
        hash_md5 = hashlib.md5()
        with open(self.fpath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    def mdval(self, key, default=None, keep_case=False):
        for k in self.metadata:
            if k.lower() == key.lower():
                key = k
        val = self.metadata.get(key, default)
        if isinstance(val, str) and not keep_case:
            val = val.lower()
        if isinstance(val, list) and len(val) > 0 and isinstance(val[0], str) and not keep_case:
            val = [v.lower() for v in val]
        return val
