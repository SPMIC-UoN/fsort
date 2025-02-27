"""
FSORT config for afirm
"""
import logging

from fsort.sorter import Sorter
from fsort.sorters import T2, T11MolliMapOrRaw, T1MolliRaw, T1SERaw, SeriesDesc, B0TwoEchos, B1, MTR, T2star

LOG = logging.getLogger(__name__)

class MDixon(Sorter):
    def __init__(self, name, seriesdesc_inc="mdixon", seriesdesc_exc=None):
        Sorter.__init__(self, name)
        self._inc = seriesdesc_inc
        self._exc = seriesdesc_exc

    def run(self):
        self.add(seriesdescription=self._inc, nvols=3)
        if self._exc:
            self.remove(seriesdescription=self._exc)
        if self.have_files():
            LOG.info(" - Found 3-volume mDIXON data")
            self.select_latest()
            self.save("water", vol=0)
            self.save("fat", vol=1)
            self.save("fat_fraction", vol=2)
            self.clear_selection()
            self.add(seriesdescription=self._inc, imagetype="T2", nvols=1)
            if self._exc:
                self.remove(seriesdescription=self._exc)
            if self.have_files():
                LOG.info(" - Found T2* map")
                self.select_latest()
                self.save("t2star", vol=0)
            else:
                LOG.warn("Could not find single-volume T2* map to go with fat/water/ff")
        else:
            # Separate files, need to do filename matching unfortunately
            LOG.info(" - Did not find 3-volume mDIXON data, doing filename matching")
            for suffix in ["RM_e1", "RM"]:
                self.add(seriesdescription=self._inc, imagetype="T2", nvols=1, fname=f"{suffix}a")
                if self._exc:
                    self.remove(seriesdescription=self._exc)
                if self.have_files():
                    self.select_latest()
                    self.save("water")
                    self.clear_selection()
                    self.add(seriesdescription=self._inc, imagetype="T2", nvols=1, fname=f"{suffix}b")
                    if self._exc:
                        self.remove(seriesdescription=self._exc)
                    self.select_latest()
                    self.save("fat")
                    self.clear_selection()
                    self.add(seriesdescription=self._inc, imagetype="T2", nvols=1, fname=f"{suffix}_real")
                    if self._exc:
                        self.remove(seriesdescription=self._exc)
                    self.select_latest()
                    self.save("fat_fraction")
                    self.clear_selection()
                    self.add(seriesdescription=self._inc, imagetype="T2", nvols=1, fname=f"{suffix}")
                    if self._exc:
                        self.remove(seriesdescription=self._exc)
                    self.remove(fname=f"{suffix}a")            
                    self.remove(fname=f"{suffix}b")            
                    self.remove(fname=f"{suffix}_real")      
                    self.select_latest()      
                    self.save("t2star")
                    break

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
    T11MolliMapOrRaw(name="t1_molli"),
    T2(),
    B0TwoEchos(add_removes=["aorta"]),
    B1(seriesdescription="B1"),
    MTR(),
    SeriesDesc("t1w"),
    SeriesDesc("t2w"),
    T2star(),
    MolliAx(),
    MolliCor(),
    MDixon(name="dixon_cor", seriesdesc_inc="cor_mdixon"),
    MDixon(name="dixon_ax", seriesdesc_inc="mdixon", seriesdesc_exc="cor_mdixon"),
    SeriesDesc("ethrive"),
]
