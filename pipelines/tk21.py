"""
FSORT config for travelling_kidney_21 study
"""
from fsort.sorters import T11MolliMapOrRaw, T2, B1, B0TwoEchos, SeriesDesc, T2star, MTR


class B0(B0TwoEchos):
    
    def run(self):
        # Special cases of SPMIC subjects with two B0 scans
        if "spmic_trav_kid" in self.outdir.lower():
            self.kwargs["select_earliest"] = True
        B0TwoEchos.run(self)

SORTERS = [
    T11MolliMapOrRaw(),
    T2(),
    B0(add_removes=["aorta"]),
    B1(seriesdescription="B1"),
    MTR(),
    SeriesDesc("t1w"),
    SeriesDesc("t2w"),
    T2star(),
]
