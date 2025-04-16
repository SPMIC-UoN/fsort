"""
FSORT config for normative data study
"""
from fsort.sorters import *
from .afirm import DWI, ASL

SORTERS = [
    T1SERaw(),
    T1MolliRaw(),
    T11MolliMapOrRaw(),
    T2(),
    B0TwoEchos(add_removes=["aorta"]),
    B1(seriesdescription="B1"),
    MTR(),
    SeriesDesc("t1w", seriesdesc=["cor_t1w", "t1w"]),
    SeriesDesc("t2w", seriesdesc=["cor_t2w", "t2w"]),
    T2star(),
    #MolliAx(),
    #MolliCor(),
    MDixon(name="dixon_cor", seriesdesc_inc="cor_mdixon"),
    MDixon(name="dixon_ax", seriesdesc_inc="mdixon", seriesdesc_exc="cor_mdixon"),
    SeriesDesc("ethrive"),
    DWI(),
    ASL(),
]
