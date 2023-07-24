#!/bin/env python
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

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

def main():
    parser = argparse.ArgumentParser(f'File pre-sorter v{__version__}', add_help=True)
    parser.add_argument('--config', help='Path to Python configuration file', required=True)
    parser.add_argument('--dicom', help='Path to DICOM input')
    parser.add_argument('--nifti', help='Path to NIFTI input')
    parser.add_argument('--output', help='Path to output folder')
    parser.add_argument('--nifti-output', help='Path to store initial NIFTI converted files. If not specified, temporary folder will be used')
    parser.add_argument('--dcm2niix-args', help='DCM2NIIX arguments for DICOM->NIFTI conversion', default="-m n -f %d_%q")
    parser.add_argument('--overwrite', action="store_true", default=False, help='If specified, overwrite any existing output')
    parser.add_argument('--debug', action="store_true", default=False, help='Enable debug output')
    options = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    _setup_logging(options)
    LOG.info(f"FSORT v{__version__}")

    if not options.dicom and not options.nifti:
        parser.error("Either NIFTI or DICOM input must be provided")
    if options.dicom and options.nifti:
        parser.error("Only one of NIFTI or DICOM input can be provided")
    
    Fsort(options).run()

if __name__ == "__main__":
    main()
