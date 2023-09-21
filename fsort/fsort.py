"""
FSORT: Class to run study-specific configuration to sort files
"""
import glob
import importlib
import logging
import os
import shutil
import subprocess
import sys

from .image_file import ImageFile
from . import xnat

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
        if self._options.xnat_host:
            xnat_sessions = xnat.get_sessions(self._options)
            for xnat_session in xnat_sessions:
                self._run_session(xnat_session.output, xnat_session.dicom)
        else:
            self._run_session(self._options.output, self._options.dicom, self._options.nifti)

    def _run_session(self, output, dicom_in=None, nifti_in=None):
        LOG.info(f"RUNNING session - output in {output}")
        if self._options.output_subfolder:
            output = os.path.join(output, self._options.output_subfolder)

        if dicom_in:
            if not nifti_in:
                nifti_in = os.path.join(output, "nifti")
            self._dcm2niix(dicom_in, nifti_in, self._options.dcm2niix_args)
        elif not nifti_in:
            raise RuntimeError("Must specify DICOM or NIFTI input folder")

        LOG.info(f" - NIFTI files in {nifti_in}")
        vendor_files = self._scan_niftis(nifti_in, allow_no_vendor=self._options.allow_no_vendor, allow_dupes=self._options.allow_dupes)
        for vendor, files in vendor_files.items():
            LOG.info(f" - Vendor: {vendor} ({len(files)} files)")

        for sorter in self._config.SORTERS:
            outdir = os.path.join(output, sorter.name)
            LOG.info(f"Sorting files for module: {sorter.name} - output in {outdir}")
            self._mkdir(outdir)
            for vendor, files in vendor_files.items():
                sorter.process_files(files, vendor, outdir)
        LOG.info(f"FSORT DONE session - output in {output}")

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
        while 1:
            # Drill down to dir with multiple scans. We will process these one at a time for better
            # resilience to dcm2niix failures
            scan_dirs = [os.path.join(dicomdir, d) for d in os.listdir(dicomdir) if os.path.isdir(os.path.join(dicomdir, d))]
            if len(scan_dirs) != 1:
                break
            dicomdir = scan_dirs[0]

        self._mkdir(niftidir)
        args = args.split()
        dcm2niix_cmd = ["dcm2niix", "-o", niftidir] + args + ["-d", "10", "-z", "y", "-b", "y"]
        LOG.info("DICOM->NIFTI conversion")
        for scan_dir in scan_dirs:
            cmd = dcm2niix_cmd + [scan_dir]
            LOG.info(" ".join(cmd))
            try:
                output = subprocess.check_output(cmd)
                LOG.debug(output)
            except subprocess.CalledProcessError as exc:
                LOG.warn(f"dcm2niix failed for {scan_dir} with exit code {exc.returncode}")
                LOG.warn(exc.output)

    def _scan_niftis(self, niftidir, allow_no_vendor=False, allow_dupes=False):
        """
        Scan NIFTI files extracting metadata in useful format for matching
        """
        vendor_files = {}
        for path, _dirs, files in os.walk(niftidir):
            for fname in files:
                if fname.endswith(".nii") or fname.endswith(".nii.gz"):
                    try:
                        fpath = os.path.join(path, fname)
                        file = ImageFile(fpath, warn_json=True)
                    except Exception:
                        LOG.exception(f"Failed to load NIFTI file {fpath} - ignoring")
                        continue

                    LOG.debug(f" - Found candidate file {fpath} for vendor {file.vendor}")
                    if file.vendor or allow_no_vendor:
                        if file.vendor not in vendor_files :
                            vendor_files[file.vendor] = []
                        dupes = [f for f in vendor_files[file.vendor] if f.hash == file.hash]
                        if dupes and not allow_dupes:
                            LOG.warn(f"{fpath} is exact duplicate of existing file {dupes[0].fname} - ignoring")
                        else:
                            if dupes:
                                LOG.warn(f"{fpath} is exact duplicate of existing file {dupes[0].fname} - keeping both")
                            vendor_files[file.vendor].append(file)

        return vendor_files
