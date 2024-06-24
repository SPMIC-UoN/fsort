
"""
FSORT: Code to do file sorting directly from an XNAT database
"""
import argparse
import logging
import os

import xnat_nott

LOG = logging.getLogger(__name__)

def get_sessions(fsort_options):
    """
    Get subject sessions based on FSORT options

    Currently only one subject at a time can be processed, this may be
    specified by name/label using options.subject or by index using
    options.subject_idx (sorted by label/ID)

    A session index can also be specified but this is optional, multiple
    sessions are processed by default

    :return: Sequence of sessions, each having attributes: output (path to
             output folder), dicom (path to downloaded DICOMs)
    """
    options = argparse.Namespace()
    for k, v in fsort_options.__dict__.items():
        if k.startswith("xnat"):
            setattr(options, k[5:], v)
    options.subject = fsort_options.subject
    options.subject_idx = fsort_options.subject_idx

    LOG.info(f" - Input data from XNAT: {options.host}")
    LOG.info(f" - Project: {options.project}")
    xnat_nott.get_credentials(options)
    xnat_nott.xnat_login(options)
    options.project = xnat_nott.get_project(options, options.project)
    if options.subject and options.subject_idx is not None:
        raise RuntimeError("Can't specify subject ID and index at the same time")
    elif not options.subject and options.subject_idx is None:
        raise RuntimeError("Must specify subject ID or subject index")
    else:
        subjects = xnat_nott.get_subjects(options, options.project)
        subjects.sort(key=lambda x: x.get('label', x.get('ID', '')).upper())
        LOG.info(f" - {len(subjects)} subjects")
        if options.subject_idx is not None:
            if options.subject_idx >= 0 and options.subject_idx < len(subjects):
                subject = subjects[options.subject_idx]
                LOG.info(f" - Selecting subject index {options.subject_idx}: ID {subjects[0]['ID']}")
            else:
                raise RuntimeError(f"Subject index out of range: {options.subject_idx}")
        else:
            subject = xnat_nott.get_subject(subjects, options.subject)

    subjid = subject.get('label', subject['ID']).upper()
    LOG.info(f" - Subject: {subjid}")

    if options.session:
        sessions = [xnat_nott.get_session(options, options.project, subject, options.session)]
    else:
        sessions = xnat_nott.get_sessions(options, options.project, subject)
        LOG.info(f" - {len(sessions)} sessions found")
        if options.session_idx is not None:
            if options.session_idx < 0 or options.session_idx >= len(sessions):
                raise RuntimeError(f"Session index out of range: {options.session_idx}")
            sessions = [sessions[options.session_idx]]

    xnat_sessions = []
    for session in sessions:
        xnat_session = argparse.Namespace()
        sessid = session.get('label', subject['ID']).upper()
        LOG.info(f" - Getting DICOMS for session: {sessid}")

        # Construct the output dir - in XNAT mode it does not include the subject ID
        if len(sessions) > 1:
            xnat_session.output = os.path.join(fsort_options.output, subjid + "_" + sessid)
        else:
            xnat_session.output = os.path.join(fsort_options.output, subjid)

        if not fsort_options.xnat_dicom_output:
            fsort_options.xnat_dicom_output = "dicom"
        xnat_session.dicom = os.path.join(xnat_session.output, fsort_options.xnat_dicom_output)

        if options.skip_downloaded and os.path.exists(xnat_session.dicom) and os.listdir(xnat_session.dicom):
            LOG.info(f" - Already downloaded - skipping")
        else:
            os.makedirs(xnat_session.output, exist_ok=True)
            xnat_nott.get_session_dicoms(options, session, xnat_session.dicom)
        xnat_sessions.append(xnat_session)

    return xnat_sessions