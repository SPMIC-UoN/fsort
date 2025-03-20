"""
FSORT config for afirm
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
            self.run()

    def run(self):
        self.add(seriesdescription="cor_t1_molli", nvols=2)
        self.select_latest()
        self.save("t1_map", vol=0)
        self.save("t1_conf", vol=1)
        

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
    MolliAx(),
    MolliCor(),
    MDixon(name="dixon_cor", seriesdesc_inc="cor_mdixon"),
    MDixon(name="dixon_ax", seriesdesc_inc="mdixon", seriesdesc_exc="cor_mdixon"),
    SeriesDesc("ethrive"),
]
