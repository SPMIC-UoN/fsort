"""
FSORT config for ceus
"""
import logging

from fsort.sorter import Sorter
from fsort.sorters import *

LOG = logging.getLogger(__name__)

class MolliAx(Sorter):
    def __init__(self):
        Sorter.__init__(self, "molli_ax")

    def run_philips(self):
        self.candidate_set = 1  # DCM2NIIX 2021
        self.add(seriesdescription="lms_molli", nvols=9)
        if self.have_files():
            self.select_latest()
            self.save("t1_map", vol=0)
            self.save("t1_conf", vol=2)
        else:
            self.run()

    def run(self):
        self.add(seriesdescription="lms_molli", nvols=2)
        self.select_latest()
        self.save("t1_map", vol=0)
        self.save("t1_conf", vol=1)
        

class MolliCor(Sorter):
    def __init__(self):
        Sorter.__init__(self, "molli_cor")

    def run_philips(self):
        self.candidate_set = 1  # DCM2NIIX 2021
        self.add(seriesdescription="cor_t1_molli", nvols=9)
        if self.have_files():
            self.select_latest()
            self.save("t1_map", vol=0)
            self.save("t1_conf", vol=2)
        else:
            self.add(seriesdescription="cor_t1_molli", nvols=10)
            if self.have_files():
                self.select_latest()
                self.save("t1_map", vol=1)
                self.save("t1_conf", vol=3)
            else:
                self.run()

    def run(self):
        self.add(seriesdescription="cor_t1_molli", nvols=2)
        self.select_latest()
        self.save("t1_map", vol=0)
        self.save("t1_conf", vol=1)



class ASL(Sorter):
    def __init__(self):
        Sorter.__init__(self, "asl")

    def run(self):
        self.add(seriesdescription="pcasl")
        self.remove(nvols=1)
        self.save("pcasl")
        self.add(seriesdescription="fair")
        self.remove(nvols=1)
        self.save("fair")


SORTERS = [
    T1MolliRaw(),
    T1MolliMapOrRaw(),
    B0TwoEchos(add_removes=["aorta"]),
    B1(seriesdescription="B1"),
    SeriesDesc("t1w", seriesdesc=["cor_t1w", "t1w"], nvols=1),
    SeriesDesc("t2w", seriesdesc=["cor_t2w", "t2w"], nvols=1),
    T2star(),
    MolliAx(),
    MolliCor(),
    dixon.RawDixon(includes={"seriesdescription" : "mdixon-quant"}, excludes={"imagetype" : "PHASE", "seriesdescription" : "12echoes"}, candidate_set=0),
    SeriesDesc("ethrive", seriesdesc=["ethrive", "e-thrive", "e_thrive"]),
    ASL(),
]
