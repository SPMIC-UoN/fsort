"""
FSORT config for memri
"""
import logging

from fsort.sorters import *

LOG = logging.getLogger(__name__)

SORTERS = [
    T1MolliRaw(),
    T1MolliMapOrRaw(),
    T2(),
    SeriesDesc("t2w", seriesdesc=["cor_t2w", "t2w"], nvols=1),
]
