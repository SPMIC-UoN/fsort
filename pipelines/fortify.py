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


class DWI(Sorter):
    def __init__(self):
        Sorter.__init__(self, "dwi")

    def run(self):
        self.candidate_set = 2  # DCM2NIIX 2024
        self.add(seriesdescription="dwi")
        self.remove(seriesdescription="flipped")
        self.remove(bval=None)
        self.remove(bval=0, match_type="len")
        self.remove(nvols=1)
        self.select_latest()
        self.save("dwi")


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


class GenericDixon(Sorter):
    def __init__(self):
        Sorter.__init__(self, "dixon_generic")

    def run(self):
        maps = {
            "water" : ["water"],
            "fat" : ["fat"],
            "fat_fraction" : ["fatfrac", "fat_frac"],
        }
        for map, keywords in maps.items():
            for kw in keywords:
                self.add(seriesdescription="dixon", nvols=1)
                self.remove(seriesdescription="mdixon")
                if self.count(seriesdescription=kw):
                    self.filter(seriesdescription=kw)
                else:
                    self.filter(imagetype=kw)
                if self.have_files():
                    self.select_latest()
                    self.save(map)
                    self.clear_selection()
                    break

class T2(Sorter):
    """
    T2 mapping data
    """
    def __init__(self, name="t2", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def run(self):
        """
        T2 data has multiple echos and possibly an extra T2 map to be discarded
        """
        self.candidate_set = self.kwargs.get("candidate_set", 0)
        num_echos = self.kwargs.get("num_echos", 10)
        seriesdesc = self.kwargs.get("seriesdesc", ("t2_mapping_resptrig", "t2_mapping", "t2 mapping", "t2map_resptrig", "t2map"))
        for desc in seriesdesc:
            LOG.info(f" - Looking for T2 mapping data with {num_echos} or {num_echos+1} volumes")
            self.add(seriesdescription=desc, nvols=num_echos)
            self.remove(echotime=None)
            if self.kwargs.get("rpts", False):
                self.filter(seriesdescription="_HO")
            else:
                self.remove(seriesdescription="_HO")
            if not self.have_files():
                self.add(seriesdescription=desc, nvols=num_echos+1)
                self.remove(echotime=None)
                if self.have_files():
                    LOG.info(f" - {num_echos+1} volumes found - removing last to discard T2 MAP image")

            if self.have_files():
                for vol in range(num_echos):
                    self.save(f"t2_e{vol+1}", vol=vol)
                break

        if not self.have_files():
            LOG.info(f" - Not found - Looking for T2 mapping data in {num_echos} or {num_echos+1} single-volume sets")
            for desc in seriesdesc:
                self.add(seriesdescription=desc, expected_number=(num_echos, num_echos+1))
                self.remove(echotime=None)
                print("Found ", self.count(), " files")
                if self.kwargs.get("rpts", False):
                    print("filtering repeats")
                    self.filter(seriesdescription="_HO")
                else:
                    print("removing repeats")
                    self.remove(seriesdescription="_HO")
                print("Found ", self.count(), " files")
                if self.have_files():
                    if self.count() == num_echos+1:
                        LOG.info(f" - {num_echos+1} echos found - trying to remove T2 MAP image")
                        self.remove(imagetype="T2 MAP")
                        if self.count() == num_echos+1:
                            LOG.warn(f"Have {num_echos+1} echos still")
                    self.save("t2_e", sort="echotime")
                    break

        if not self.have_files():
            LOG.warn("No T2 mapping data found")
            

class T2star(Sorter):
    """
    T2* mapping data
    
    Need multiple echos (12 in AFIRM), real part
    """
    def __init__(self, name="t2star", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def _get_files(self, seriesdesc):
        self.add(seriesdescription=seriesdesc, nvols=1)
        self.remove(imagetype="PHASE")
        self.remove(seriesdescription="PHASE")
        self.remove(imagetype="REAL")
        self.remove(imagetype="IMAGINARY")
        self.remove(imagetype="DERIVED")
        self.remove(echotime=None)
        self.remove(fname="_ph")
        if self.kwargs.get("rpts", False):
            self.filter(seriesdescription="_HO")
        else:
            self.remove(seriesdescription="_HO")

    def run(self):
        self._get_files("t2star")
        if not self.have_files():
            LOG.info(" - No T2star data found, checking for T2*")
            self._get_files("t2*")
            if not self.have_files():
                LOG.info(" - No T2* data found, checking for T2")
                self._get_files("t2")
                for remove in ("t2_mapping", "t2 mapping", "t2map_resptrig", "t2map"):
                    self.remove(seriesdescription=remove)

        for hires_identifier in ("highres", "hires", "high_res"):
            if self.count(seriesdescription=hires_identifier) > 0:
                LOG.info(f" - Found high-res data with flag {hires_identifier}, keeping only data with this flag")
                self.filter(seriesdescription=hires_identifier)
        if self.count(imagetype="NORM") > 0:
            LOG.info(f" - Found normalised data, keeping only data with this flag")
            self.filter(imagetype="NORM")

        # FIXME ideally we want to check for T1 overlap as in renal_preproc code
        self.group("echotime", allow_none=False)
        self.select_one("seriesnumber", last=False)
        self.save("t2star_e", sort="echotime")

class T1MolliMapOrRaw(T1MolliMapOrRaw):
    def _add_std(self):
        self.add(seriesdescription="molli", imagetype="T1_MAP")
        self.add(seriesdescription="molli", imagetype="T1 MAP")
        if not self.have_files():
            self.add(seriesdescription="molli", imagetype="T1")
            self.filter(imagetype="MAP")
        if not self.have_files():
            self.add(seriesdescription="molli", imagetype="MIXED")
        if not self.have_files():
            self.add(seriesdescription="molli")
        if self.kwargs.get("rpts", False):
            self.filter(seriesdescription="_HO")
        else:
            self.remove(seriesdescription="_HO")


class T1MolliRaw(Sorter):
    """
    T1 MOLLI raw mapping data
    """
    def __init__(self, name="t1_molli_raw", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def run(self):
        self.add(seriesdescription="molli", nvols=8)
        if self.kwargs.get("rpts", False):
            self.filter(seriesdescription="_HO")
        else:
            self.remove(seriesdescription="_HO")
        self.remove(seriesdescription="6.5", reason="6.5mm slice")
        self.remove(seriesdescription="flipped")
        self.remove(imagetype="phase")
        self.remove(nslices=3, reason="3-slice heart scan")
        self.remove(seriesdescription="500", reason="TD500 scan addition to TD0 scan")
        self.remove(seriesdescription="DelREc", reason="delayed reconstruction")
        if self.count(seriesdescription="highres") > 0:
            self.filter(seriesdescription="highres", reason="Not high-res and we have other data that is")
        if self.count(multislice=True) > 0:
            self.filter(multislice=True, reason="Not multi-slice and we have other data that is")
        self.group("affinedata")
        self.select_latest()
        self.save("t1_molli_raw")

class T2wDixon(Sorter):
    """
    T2w Dixon data
    """
    def __init__(self, name="dixon", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def run(self):
        self.add(seriesdescription="dixon")
        print("Found ", self.count(), " files")
        self.filter(nvols=4)
        print("Found ", self.count(), " files")
        self.select_latest()
        self.save("water", vol=0)
        self.save("fat", vol=1)
        self.save("ip", vol=2)
        self.save("op", vol=3)

SORTERS = [
    T1SERaw(),
    T1MolliRaw(rpts=False),
    T1MolliRaw(name="t1_molli_rpt_raw", rpts=True),
    T1MolliMapOrRaw(rpts=False),
    T1MolliMapOrRaw(name="t1_molli_rpt", rpts=True),
    T2(rpts=False),
    T2(name="t2_rpt", rpts=True, seriesdesc=("t2_mapping_resptrig_ho", "t2_mapping_ho", "t2 mapping_ho", "t2map_resptrig_ho", "t2map_ho")),
    T2star(rpts=False),
    T2star(name="t2star_rpt", rpts=True),
    B0TwoEchos(add_removes=["aorta"]),
    SeriesDesc("t1w", seriesdesc=["cor_t1w", "t1w"], nvols=1),
    SeriesDesc("t2w", seriesdesc=["cor_t2w", "t2w"], nvols=1),
    T2wDixon(),
    MolliCor(),
    DWI(),
    ASL(),
]
