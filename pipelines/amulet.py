"""
File sorter for amulet
"""
import logging

from fsort import Sorter, run
from fsort.sorters import SeriesDesc, dixon
LOG = logging.getLogger(__name__)

SORTERS = [
    SeriesDesc("t1w_in", seriesdesc=["T1W_dualecho_core_in_ND"], nvols=1),
    SeriesDesc("t1w_out", seriesdesc=["T1W_dualecho_core_opp_ND"], nvols=1),
    SeriesDesc("t1w_fat", seriesdesc=["T1W_dualecho_core_F_ND"], nvols=1),
    SeriesDesc("t1w_water", seriesdesc=["T1W_dualecho_core_W_ND"], nvols=1),
    SeriesDesc("t1w_fs", seriesdesc=["T1W_FS_core"], nvols=1),
    SeriesDesc("t2w_fs", seriesdesc=["T2W_FS_core"], nvols=1),
    SeriesDesc("t2w_nofs", seriesdesc=["T2W_core"], nvols=1),
    SeriesDesc("dwi", seriesdesc=["DWI_core_EP"]),
    SeriesDesc("dwi_adc", seriesdesc=["DWI_core_ADC"], nvols=1),
    dixon.RawDixon(includes={"seriesdescription" : "mdixon-quant"}, excludes={"imagetype" : "PHASE", "seriesdescription" : "12echoes"}, candidate_set=0),
]

if __name__ == "__main__":
    run(__file__)
