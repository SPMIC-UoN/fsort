import logging

from fsort import Sorter, run
from fsort.sorters import SeriesDesc, ScannerT2Map, T1SERaw, T2, MTR

LOG = logging.getLogger(__name__)

SORTERS = [
    SeriesDesc("dti_ap", seriesdesc=["DTI_AP"]),
    SeriesDesc("dti_pa", seriesdesc=["DTI_PA"]),
    SeriesDesc("mprage", seriesdesc=["MPRAGE"]),
    SeriesDesc("flair", seriesdesc=["FLAIR"]),
]

if __name__ == "__main__":
    run(__file__)
