"""
FSORT: Run study-specific FSORT configurations
"""
import datetime
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
        if options.config:
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
        else:
            LOG.info("No pipeline sorter provided - will perform dcm2niix only")
            self._config = None

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
        self._mkdir(output, wipe=False)  # Do not wipe in case we are re-using dicoms/niftis
        logfile = os.path.join(output, "logfile.txt")
        if os.path.exists(logfile):
            os.remove(logfile)
        handler = logging.FileHandler(logfile)
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logging.getLogger().addHandler(handler)
        LOG.info(f" - Output dir: {output}")

        nifti_sets = []
        if dicom_in:
            LOG.info(f"DICOM->NIFTI conversion: DICOMS in {dicom_in}")
            nifti_output = os.path.join(output, "nifti")
            if not niftidirs:
                niftidirs = []

            for idx, dcm2niix in enumerate(self._options.dcm2niix):
                niftidir_dcm2niix = os.path.join(nifti_output, f"dcm2niix_{idx}")
                if self._options.skip_dcm2niix and os.path.exists(niftidir_dcm2niix) and os.listdir(niftidir_dcm2niix):
                    LOG.info(f" - NIFTI files already found in {niftidir_dcm2niix} - skipping dcm2niix conversion")
                else:
                    LOG.info(f" - Converting to nifti using {dcm2niix} output in {niftidir_dcm2niix}")
                    self._dcm2niix(dicom_in, niftidir_dcm2niix, dcm2niix, self._options.dcm2niix_args)

                niftidirs_dcm2niix = list(niftidirs) + [niftidir_dcm2niix]
                nifti_sets.append(niftidirs_dcm2niix)
        elif not niftidirs:
            raise RuntimeError("Must specify DICOM or NIFTI input folder")
        else:
            nifti_sets.append(niftidirs)

        vendor_files = {}
        for idx, niftidirs in enumerate(nifti_sets):
            LOG.info(f"Scanning NIFTI files in {niftidirs}")
            set_vendor_files = self._scan_niftis(niftidirs, allow_no_vendor=self._options.allow_no_vendor, allow_dupes=self._options.allow_dupes)
            if not set_vendor_files:
                LOG.warn(f"No session files found")
            else:
                for vendor, files in set_vendor_files.items():
                    LOG.info(f" - Vendor: {vendor} ({len(files)} files)")
                    if dicom_in:
                        LOG.info(f" - Linking DICOM data")
                        self._link_niftis_to_dicoms(files, dicom_in)
                    if vendor not in vendor_files:
                        vendor_files[vendor] = {}
                    vendor_files[vendor][idx] = files

        if self._config is not None:
            for sorter in self._config.SORTERS:
                outdir = os.path.join(output, sorter.name)
                timestamp = self._timestamp()
                LOG.info(f"FSORT RUNNING {sorter.name.upper()} -> {outdir} : start time {timestamp}")
                self._mkdir(outdir)
                for vendor, file_sets in vendor_files.items():
                    sorter.process_files(file_sets, vendor, outdir)
                timestamp = self._timestamp()
                LOG.info(f"FSORT DONE {sorter.name.upper()} : end time {timestamp}")
        LOG.info(f"FSORT DONE -> {output}")

    def _timestamp(self):
        return str(datetime.datetime.now())

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

    def _mkdir(self, dirname, wipe=True):
        """
        Create an output directory, checking if it exists and whether we can overwrite it
        """
        if os.path.exists(dirname):
            if not self._options.overwrite:
                raise RuntimeError(f"Output directory {dirname} already exists - use --overwrite to remove")
            elif wipe:
                shutil.rmtree(dirname)
            else:
                return

        os.makedirs(dirname, mode=0o777)

    def _dcm2niix(self, dicomdir, niftidir, dcm2niix_exec, args):
        """
        Run DCM2NIIX if we are using DICOM input

        We walk the dicomdir tree and run dcm2niix on every folder that contains files
        """
        self._mkdir(niftidir)
        args = args.split()
        dcm2niix_cmd = [dcm2niix_exec, "-o", niftidir] + args + ["-d", "0", "-z", "y", "-b", "y"]
        scandirs = []
        num_files = 0
        for root, _dirs, files in os.walk(dicomdir, topdown=False, followlinks=True):
            num_files += len(files)
            if files:
                scandir = Path(os.path.join(dicomdir, root))
                for scandir_done in scandirs:
                    if scandir_done in scandir.parents:
                        continue
                cmd = dcm2niix_cmd + [str(scandir)]
                LOG.debug(f" - Converting DICOMS in {scandir}")
                LOG.debug(" ".join(cmd))
                try:
                    output = subprocess.check_output(cmd)
                    LOG.debug(output)
                except subprocess.CalledProcessError as exc:
                    LOG.warn(f"{dcm2niix_exec} failed for {scandir} with exit code {exc.returncode}")
                    LOG.warn(exc.output)
        
        with open(os.path.join(niftidir, "num_dicoms.txt"), "w") as f:
            f.write("%i\n" % num_files)

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
            for path, _dirs, files in os.walk(niftidir, followlinks=True):
                for fname in files:
                    if fname.endswith(".nii") or fname.endswith(".nii.gz"):
                        try:
                            fpath = os.path.join(path, fname)
                            file = ImageFile(fpath, warn_json=True)
                        except Exception:
                            LOG.exception(f"Failed to load NIFTI file {fpath} - ignoring")
                            continue

                        LOG.debug(f" - Found candidate file {fpath} for vendor {file.vendor}")
                        if file.vendor not in vendor_files :
                            vendor_files[file.vendor] = []
                        if not allow_dupes:
                            dupes = [f for f in vendor_files[file.vendor] if f.hash == file.hash]
                            if dupes:
                                LOG.warn(f"{fpath} is exact duplicate of existing file {dupes[0].fname} - ignoring")
                                continue
                        vendor_files[file.vendor].append(file)

        no_vendor_files = vendor_files.pop(None, [])
        if allow_no_vendor and no_vendor_files:
            # No vendor files are added to all vendors
            for vendor, files in vendor_files.items():
                vendor_files[vendor] += no_vendor_files
                LOG.info(f" - Found {len(no_vendor_files)} files with no vendor - adding to {vendor} {no_vendor_files}")

        return vendor_files

    def _link_niftis_to_dicoms(self, nifti_files, dicomdir):
        tags_to_scan = {
            "InstanceCreationTime" : (0x0008, 0x0013),
            "InversionTimeDelay" : (0x2005, 0x1572),
            "NumberInversionDelays" : (0x2005, 0x1571),
            "HeartRate" : (0x0018,0x1088),
            "InversionTimeDelay+" : (0x0018, 0x0082),
        }
        
        dicom_tag_dict = {}
        for root, _dirs, files in os.walk(dicomdir, topdown=False, followlinks=True):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    import pydicom
                    dcm = pydicom.dcmread(fpath)
                    series_number = dcm["SeriesNumber"].value
                    if series_number not in dicom_tag_dict:
                        dicom_tag_dict[series_number] = []
                    dcm_metadata = {}
                    for name, tag in tags_to_scan.items():
                        name = name.replace("+", "")
                        md = dcm.get(tag, None)
                        if md:
                            dcm_metadata[name] = md.value
                    dicom_tag_dict[series_number].append(dcm_metadata)
                except:
                    # May not be a DICOM
                    pass

        for series_number, metadata in dicom_tag_dict.items():
            metadata.sort(key=lambda x: x.get("InstanceCreationTime", 0))

        for img in nifti_files:
            if img.seriesnumber in dicom_tag_dict:
                dcm_metadata = dicom_tag_dict[img.seriesnumber]
                for name in tags_to_scan:
                    name = name.replace("+", "")
                    # FIXME is it always right to sort by value?
                    img.metadata[name] = sorted([v[name] for v in dcm_metadata if name in v])
