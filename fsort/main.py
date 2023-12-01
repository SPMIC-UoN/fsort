"""
FSORT: File pre-sorter for imaging processing pipelines
"""
import argparse
import sys
import logging

from ._version import __version__
from .fsort import Fsort

LOG = logging.getLogger(__name__)

def _setup_logging(args):
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

def run(config_fname):
    sys.argv.append(f"--config={config_fname}")
    main()

def main():
    """
    FSORT command line entry point
    """
    parser = argparse.ArgumentParser(f'File pre-sorter v{__version__}', add_help=True)
    parser.add_argument('--config', help='Path to Python configuration file', required=True)
    parser.add_argument('--dicom', help='Path to DICOM input')
    parser.add_argument('--nifti', help='Path to NIFTI input')
    parser.add_argument("--skip-dcm2niix", help="Skip DCM2NIIX conversion where NIFTI dir already exists and contains files", action="store_true", default=False)
    parser.add_argument("--xnat-host", help="XNAT host url")
    parser.add_argument("--xnat-project", help="Project ID")
    parser.add_argument("--xnat-subject", help="Subject ID")
    parser.add_argument("--xnat-subject-idx", type=int, help="Specify subject by index number (starting at zero)")
    parser.add_argument("--xnat-session", help="Session ID")
    parser.add_argument("--xnat-session-idx", type=int, help="Session index (starting at zero)")
    parser.add_argument('--xnat-dicom-output', help='Path to store initial DICOM downloaded files. If not specified will use dicom')
    parser.add_argument("--xnat-user", help="XNAT username. If not supplied, environment variable XNAT_USER will be used or interactive prompt provided")
    parser.add_argument("--xnat-skip-downloaded", help="Skip subjects where DICOM dir already exists", action="store_true", default=False)
    parser.add_argument('--output', help='Path to output folder')
    parser.add_argument('--output-subfolder', help='Subfolder relative to output')
    parser.add_argument('--nifti-output', help='Path (relative to output) to store initial NIFTI converted files. If not specified, will use nifti')
    parser.add_argument('--dcm2niix-args', help='DCM2NIIX arguments for DICOM->NIFTI conversion', default="-m n -f %d_%q")
    parser.add_argument('--allow-no-vendor', action="store_true", default=False, help='If specified, process files even when no vendor can be identified')
    parser.add_argument('--allow-dupes', action="store_true", default=False, help='If specified, process files even when another file was found with same image contents')
    parser.add_argument('--overwrite', action="store_true", default=False, help='If specified, overwrite any existing output')
    parser.add_argument('--debug', action="store_true", default=False, help='Enable debug output')
    options = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    _setup_logging(options)
    LOG.info(f"FSORT v{__version__}")

    if not options.dicom and not options.nifti and not options.xnat_host:
        parser.error("Either NIFTI, DICOM or XNAT input must be provided")
    if sum([bool(v) for v in (options.dicom, options.nifti, options.xnat_host)]) > 1:
        parser.error("Only one of NIFTI, DICOM or XNAT input can be provided")
    
    Fsort(options).run()

if __name__ == "__main__":
    main()
