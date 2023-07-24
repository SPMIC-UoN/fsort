"""
FSORT: Run configuration to sort files
"""
import glob
import importlib
import json
import logging
import math
import os
import shutil
import subprocess
import sys

import nibabel as nib

LOG = logging.getLogger(__name__)
FLOAT_TOL = 1e-3

class CandidateFile:
    def __init__(self, fname, nii, metadata):
        self.fname = os.path.abspath(os.path.normpath(fname))
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

class Fsort:
    """
    """
    def __init__(self, options):
        self._options = options
        options.config = os.path.abspath(os.path.normpath(options.config))
        config_dirname, config_fname = os.path.split(options.config)
        try:
            LOG.info(f"Loading sorter configuration from {options.config}")
            sys.path.append(config_dirname)
            self._config = importlib.import_module(config_fname.replace(".py", ""))
            sys.path.remove(config_dirname)
        except ImportError:
            LOG.exception("Loading config")
            raise ValueError(f"Could not load configuration {options.config} - make sure file exists and has extension .py")

    def run(self):
        if self._options.dicom:
            nifti_dir = self._options.nifti_output
            if not nifti_dir:
                nifti_dir = os.path.join(self._options.output, "dcm2niix")
            self._dcm2niix(self._options.dicom, nifti_dir, self._options.dcm2niix_args)
        else:
            nifti_dir = self._options.nifti
        LOG.info(f"NIFTI files in {nifti_dir}")
        
        vendor_files = self._scan_niftis(nifti_dir)
        for vendor, files in vendor_files.items():
            LOG.info(f" - Vendor: {vendor} ({len(files)} files)")

        for sorter in self._config.SORTERS:
            outdir = os.path.join(self._options.output, sorter.name)
            LOG.info(f"Sorting files for module: {sorter.name} - output in {outdir}")
            self._mkdir(outdir)
            for vendor, files in vendor_files.items():
                sorter.process_files(files, vendor, outdir)

    def _mkdir(self, dirname):
        """
        Create an output directory, checking if it exists and whether we can overwrite it
        """
        if os.path.exists(dirname):
            if not self._options.overwrite:
                raise RuntimeError(f"Output directory {dirname} already exists - use --overwrite to remove")
            else:
                shutil.rmtree(dirname)

        os.makedirs(dirname, mode=0o777)

    def _dcm2niix(self, dicomdir, niftidir, args):
        """
        Run DCM2NIIX if we are using DICOM input
        """
        self._mkdir(niftidir)
        args = args.split()
        cmd = ["dcm2niix", "-o", niftidir] + args + ["-d", "10", "-z", "y", "-b", "y", dicomdir]
        LOG.info("DICOM->NIFTI conversion")
        LOG.info(" ".join(cmd))
        output = subprocess.check_output(cmd)
        LOG.debug(output)

    def _scan_niftis(self, niftidir, allow_no_vendor=False):
        """
        Scan NIFTI files extracting metadata in useful format for matching
        """
        files = {}
        for nii_ext in (".nii", ".nii.gz"):
            for fname in glob.glob(os.path.join(niftidir, f"*{nii_ext}")):
                try:
                    nii = nib.load(fname)
                except:
                    LOG.exception(f"Failed to load NIFTI file {fname} - ignoring")
                    continue

                fname_json = fname.replace(nii_ext, ".json")
                if os.path.exists(fname_json):
                    try:
                        with open(fname_json) as f:
                            md = json.load(f)
                    except:
                        LOG.exception(f"Failed to load JSON sidecar {fname_json} - metadata matching may not work")
                        md = {}
                else:
                    LOG.warn(f"No .JSON metadata for NIFTI file {fname} - metadata matching may not work")
                    md = {}

                file = CandidateFile(fname, nii, md)
                LOG.debug(f" - Found candidate file {fname} for vendor {file.vendor}")
                if file.vendor or allow_no_vendor:
                    if file.vendor not in files :
                        files[file.vendor] = []
                    files[file.vendor].append(file)

        return files