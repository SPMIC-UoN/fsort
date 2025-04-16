"""
FSORT config for travelling_kidney_21 study
"""
from fsort.sorters import *
from afirm import DWI, ASL

class B0Tk21Special(B0TwoEchos):
    
    def run(self):
        # Special cases of SPMIC subjects with two B0 scans
        if "spmic_trav_kid" in self.outdir.lower():
            self.kwargs["select_earliest"] = True
        B0TwoEchos.run(self)

SORTERS = [
    T1SERaw(),
    T1MolliRaw(),
    T11MolliMapOrRaw(),
    T2(),
    B0Tk21Special(add_removes=["aorta"]),
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
