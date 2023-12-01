"""
FSORT

FSORT is a tool for doing pre-sorting of NIFTI or DICOM files prior to running a processing pipeline.

The purpose of FSORT is to:

 - Identify the files that play particular roles in the analysis and give them standardized names
 - Deal with any vendor-specific differences in the way data is acquired, e.g. scaling or selecting
   appropriate volumes from 4D data

A configuration file is required for each application, this defines a list of 'sorters' that
each identify a particular kind of file, e.g. T1 mapping.

Sorters are derived from a base class that provides methods for identifying files based on metadata
attributes (e.g. ImageType), grouping them based on attributes, selection of particular volumes, most
recent matching file, etc, scaling the data in the file based on a constant factor or another attribute
and saving the resulting file(s) under standard names.

It is possible to use filename as part of the matching process but this is discouraged - it is more
reliable to use metadata instead. Filename matching should only be used when the source data is in
NIFTI and no JSON sidecar metadata is available.
"""
from .sorter import Sorter
from .main import run
