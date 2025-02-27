"""
FSORT config for normative data study
"""
from fsort.sorters import T11MolliMapOrRaw, T2, B1, B0TwoEchos, SeriesDesc, T2star, MTR

SORTERS = [
    T11MolliMapOrRaw(),
    T2(),
    B0TwoEchos(add_removes=["aorta"]),
    B1(seriesdescription="B1"),
    MTR(),
    SeriesDesc("t1w"),
    SeriesDesc("t2w"),
    T2star(),
]
