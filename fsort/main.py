"""
FSORT: File pre-sorter for imaging processing pipelines
"""
import argparse
import os
import sys
import logging

from ._version import __version__
from .fsort import Fsort, timestamp
from . import xnat

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
    parser.add_argument('--dicom', help='Path to DICOM input. If --input or --subjects-file-has-dir this is a relative path')
    parser.add_argument('--nifti', help='Path to NIFTI input. If --input or --subjects-file-has-dir these are relative paths', nargs="*")
    parser.add_argument("--input", "--subjects-dir", help="Input base directory. Subject ID will be appended if not already present")
    parser.add_argument("--subjects-file", help="File containing subject IDs and optionally tab separated input directories")
    parser.add_argument("--subjects-file-has-dirs", action="store_true", default=False, help="File containing subject IDs also has input directories")
    parser.add_argument("--subject", "--xnat-subject", help="Subject ID")
    parser.add_argument("--subject-idx", "--xnat-subject-idx", type=int, help="Specify subject by zero-based index number into --subjects-file or --input subdirs")
    parser.add_argument("--xnat-host", help="XNAT host url")
    parser.add_argument("--xnat-project", help="Project ID")
    parser.add_argument("--xnat-session", help="Session ID")
    parser.add_argument("--xnat-session-idx", type=int, help="Session index (starting at zero)")
    parser.add_argument('--xnat-dicom-output', help='Path to store initial DICOM downloaded files. If not specified will use dicom')
    parser.add_argument("--xnat-user", help="XNAT username. If not supplied, environment variable XNAT_USER will be used or interactive prompt provided")
    parser.add_argument("--xnat-skip-downloaded", help="Skip subjects where DICOM dir already exists", action="store_true", default=False)
    parser.add_argument('--output', help='Path to output folder. If not specified, --input will be used. Subject ID will be appended if not already present')
    parser.add_argument('--output-subfolder', help='Subfolder relative to output')
    parser.add_argument('--nifti-output', help='Path (relative to output) to store initial NIFTI converted files. If not specified, will use nifti')
    parser.add_argument("--skip-dcm2niix", help="Skip DCM2NIIX conversion where NIFTI dir already exists and contains files", action="store_true", default=False)
    parser.add_argument('--dcm2niix', help='One or more dcm2niix executables. Sorters can select which to use', nargs="*", default=["dcm2niix"])
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
    LOG.info(f"FSORT v{__version__}: start time {timestamp()}")

    if not options.dicom and not options.nifti and not options.xnat_host:
        # Assum DICOMS under subject input dir
        options.dicom = "."
    if sum([bool(v) for v in (options.dicom, options.nifti, options.xnat_host)]) > 1:
        parser.error("Only one of NIFTI, DICOM or XNAT input can be provided")
    if options.subject and options.subject_idx:
        parser.error("Only one of SUBJECT and SUBJECT_IDX can be provided")
    if (options.input or options.subjects_file) and not (options.subject or options.subject_idx is not None):
        parser.error("INPUT/SUBJECTS_FILE provided, but neither SUBJECT or SUBJECT_IDX was given")
    if options.subjects_file_has_dirs and not options.subjects_file:
        parser.error("No subjects file given, but --subjects-file-has-dirs specified")
    if options.subject_idx is not None and options.subject_idx < 0:
        parser.error("SUBJECT_IDX must be >= 0")

    fsort = Fsort(options)
    if options.xnat_host:
        xnat_sessions = xnat.get_sessions(options)
        for xnat_session in xnat_sessions:
            fsort.run(xnat_session.output, xnat_session.dicom)
    else:
        if options.subject_idx is not None:
            # Identify subject from index number
            if options.subjects_file:
                with open(options.subjects_file, "r") as f:
                    subjects = [l.strip() for l in f.readlines() if l.strip()]
            elif options.input:
                subjects = [d for d in os.listdir(options.input) if os.path.isdir(os.path.join(options.input, d))]
                subjects = sorted(subjects)
            else:
                parser.error("--subject-idx given but neither --subjects-file nor --input was specified")
            if options.subject_idx >= len(subjects):
                parser.error(f"Invalid --subject-idx {options.subject_idx} - only {len(subjects)} subjects found")

            options.subject = subjects[options.subject_idx]
            if options.subjects_file_has_dirs:
                options.subject, options.input = options.subject.split("\t", 1)
            LOG.info(f" - Subject ID: {options.subject}")

        if options.input and not options.subjects_file_has_dirs:
            # Input base directory may need subject appending
            if options.subject and not options.input.strip().endswith(options.subject):
                options.input = os.path.join(options.input, options.subject)

        if options.input or options.subjects_file_has_dirs:
            # DICOM/NIFTI paths are relative if we have a subject input directory from elsewhere
            if options.dicom:
                options.dicom = os.path.join(options.input, options.dicom)
            if options.nifti:
                options.nifti = [os.path.join(options.input, n) for n in options.nifti]

        if not options.output:
            options.output = options.input
        elif options.subject and not options.output.strip().endswith(options.subject):
            options.output = os.path.join(options.output, options.subject)

        fsort.run(options.output, options.dicom, options.nifti)

if __name__ == "__main__":
    main()
