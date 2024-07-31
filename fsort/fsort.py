"""
FSORT: Run study-specific FSORT configurations
"""
import importlib
import logging
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .image_file import ImageFile

LOG = logging.getLogger(__name__)

class Fsort:
    """
    Class to run study-specific FSORT configurations

    This class takes a configuration file that defines a set of Sorter instances
    and runs them on input data.

    The input data may come from a directory containing DICOM or NIFTI files
    or from an XNAT instance.
    """

    def __init__(self, options):
        """
        Loads configuration from the options.config attribute
        
        This is a Python module defining sorters for the Fsort run
        """
        self._options = options
        self._logfile_handler = None
        options.config = os.path.abspath(os.path.normpath(options.config))
        config_dirname, config_fname = os.path.split(options.config)

        try:
            LOG.info(f"Loading sorter configuration from {options.config}")
            sys.path.append(config_dirname)
            self._config = importlib.import_module(config_fname.replace(".py", ""))
        except ImportError:
            LOG.exception("Loading config")
            raise ValueError(f"Could not load configuration {options.config} - make sure file exists and has extension .py")
        finally:
            sys.path.remove(config_dirname)

    def run(self, output, dicom_in=None, niftidirs=None):
        """
        Run file sorting on a single subject session

        We do DICOM->NIFTI conversion if required, and then scan the NIFTI
        files to identify the vendor (hopefully only one!) and read the
        metadata for each file. Then we pass the file list to each of the
        Sorter modules in turn to extract and rename the files it needs
        """
        if self._options.output_subfolder:
            output = os.path.join(output, self._options.output_subfolder)
        self._mkdir(output)
        logfile = os.path.join(output, "logfile.txt")
        if os.path.exists(logfile):
            os.remove(logfile)
        handler = logging.FileHandler(logfile)
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logging.getLogger().addHandler(handler)
        LOG.info(f" - Output dir: {output}")

        if dicom_in:
            LOG.info("DICOM->NIFTI conversion")
            if not niftidirs:
                niftidirs = [os.path.join(output, "nifti")]
            elif len(niftidirs) > 1:
                raise ValueError("Only one NIFTI dir allowed when using DICOM source data")

            niftidir = niftidirs[0]
            if self._options.skip_dcm2niix and os.path.exists(niftidir) and os.listdir(niftidir):
                LOG.info(f" - NIFTI files already found in {niftidir} - skipping dcm2niix conversion")
            else:
                self._dcm2niix(dicom_in, niftidir, self._options.dcm2niix_args)
        elif not niftidirs:
            raise RuntimeError("Must specify DICOM or NIFTI input folder")

        LOG.info(f"Scanning NIFTI files in {niftidirs}")
        vendor_files = self._scan_niftis(niftidirs, allow_no_vendor=self._options.allow_no_vendor, allow_dupes=self._options.allow_dupes)
        if not vendor_files:
            LOG.warn(f"No session files found")
        else:
            for vendor, files in vendor_files.items():
                LOG.info(f" - Vendor: {vendor} ({len(files)} files)")
            
            for sorter in self._config.SORTERS:
                outdir = os.path.join(output, sorter.name)
                LOG.info(f"FSORT MODULE: {sorter.name.upper()} -> {outdir}")
                self._mkdir(outdir)
                for vendor, files in vendor_files.items():
                    sorter.process_files(files, vendor, outdir)
                LOG.info(f"FSORT MODULE: {sorter.name.upper()} DONE")
        LOG.info(f"FSORT DONE -> {output}")

    def _start_logfile(self, output_folder):
        """
        Set up a logfile to capture logging output in the output folder

        We might be running multiple sessions, so remove any existing handler
        first (from a previous session)
        """
        logfile = os.path.join(output_folder, "logfile.txt")
        if os.path.exists(logfile):
            os.remove(logfile)
        if self._logfile_handler is not None:
            logging.getLogger().removeHandler(self._logfile_handler)
        self._logfile_handler = logging.FileHandler(logfile)
        self._logfile_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logging.getLogger().addHandler(self._logfile_handler)

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

        We walk the dicomdir tree and run dcm2niix on every folder that contains files
        """
        self._mkdir(niftidir)
        args = args.split()
        dcm2niix_cmd = ["dcm2niix", "-o", niftidir] + args + ["-d", "10", "-z", "y", "-b", "y"]
        scandirs = []
        for root, _dirs, files in os.walk(dicomdir, topdown=False):
            if files:
                scandir = Path(os.path.join(dicomdir, root))
                for scandir_done in scandirs:
                    if scandir_done in scandir.parents:
                        continue
                cmd = dcm2niix_cmd + [str(scandir)]
                LOG.info(f" - Converting DICOMS in {scandir}")
                LOG.debug(" ".join(cmd))
                try:
                    output = subprocess.check_output(cmd)
                    LOG.debug(output)
                except subprocess.CalledProcessError as exc:
                    LOG.warn(f"dcm2niix failed for {scandir} with exit code {exc.returncode}")
                    LOG.warn(exc.output)

    def _scan_niftis(self, niftidirs, allow_no_vendor=False, allow_dupes=False):
        """
        Scan NIFTI files extracting metadata in useful format for matching

        :param niftidir: Path to folder containing Nifti files (not necessarily flat)
        :param allow_no_vendor: If True, keep files with no vendor in metadata
        :param allow_dupes: If True, keep files where the image content exactly matches another file
        :return: Mapping from vendor name to list of ImageFile instances
        """
        vendor_files = {}
        for niftidir in niftidirs:
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
