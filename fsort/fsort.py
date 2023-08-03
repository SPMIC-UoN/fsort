"""
FSORT: Class to run study-specific configuration to sort files
"""
import glob
import importlib
import json
import logging
import os
import shutil
import subprocess
import sys

import nibabel as nib

from .candidate_file import CandidateFile

LOG = logging.getLogger(__name__)

class Fsort:
    """
    File Sorter
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
