"""
FSORT config for travelling_kidney_21 study
"""
import logging

from fsort.sorter import Sorter

from afirm import B0, B1, MTR, T1w, T2w, T2star

LOG = logging.getLogger(__name__)

class T2(Sorter):
    """
    T2 mapping data
    """
    def __init__(self):
        Sorter.__init__(self, "t2")

    def run(self):
        """
        T2 data has 10 echos but may have 11 vols (last is T2 map - ignore)
        """
        for desc in ("t2_mapping", "t2 mapping", "t2map_resptrig", "t2map"):
            self.add(seriesdescription=desc, expected_number=(10, 11))
            self.remove(echotime=None)
            if self.have_files():
                break
        if not self.have_files():
            LOG.warn("No T2 mapping data found")
        if self.count() == 11:
            LOG.info(" - 11 echos found - trying to remove T2 MAP image")
            self.remove(imagetype="T2 MAP")
            if self.count() == 11:
                LOG.warn("Have 11 echos still")

        self.save("t2_e", sort="echotime")

class T1(Sorter):
    """
    T1 MOLLI mapping data
    
    This is quite vendor specific, plus for GE we may only get
    'raw' data that needs subsequent reconstruction to obtain T1 map
    """
    def __init__(self):
        Sorter.__init__(self, "t1")

    def _add_std(self):
        self.add(seriesdescription="molli", imagetype="T1_MAP")
        self.add(seriesdescription="molli", imagetype="T1 MAP")
        if not self.have_files():
            self.add(seriesdescription="molli", imagetype="T1")
            self.filter(imagetype="MAP")
        if not self.have_files():
            self.add(seriesdescription="molli", imagetype="MIXED")

    def _filter_std(self):
        self.remove(nslices=3, reason="3-slice heart scan")
        self.remove(seriesdescription="500", reason="TD500 scan addition to TD0 scan")
        self.remove(seriesdescription="DelREc", reason="delayed reconstruction")
        self.remove(seriesdescription="6.5", reason="6.5mm slice")
        if self.count(seriesdescription="highres") > 0:
            self.filter(seriesdescription="highres", reason="Not high-res and we have other data that is")
        if self.count(multislice=True) > 0:
            self.filter(multislice=True, reason="Not multi-slice and we have other data that is")

    def run_philips(self):
        self._add_std()
        self._filter_std()
        self.group("affinedata")
        self.select_latest()

        if self.count(nvols=1) > 0:
            nvols, map_vol, conf_vol = 1, 0, 0
        if self.count(nvols=10) > 0:
            nvols, map_vol, conf_vol = 10, 1, 3
        elif self.count(nvols=9) > 0:
            nvols, map_vol, conf_vol = 9, 0, 2
        elif self.count(nvols=2) > 0:
            nvols, map_vol, conf_vol = 2, 0, 1
        else:
            nvols, map_vol, conf_vol = "UNKNOWN", 0, 0
            
        LOG.info(f" - Found {nvols}-volume data from Philips - taking volume {map_vol} for T1 map, {conf_vol} for confidence")
        self.save("t1_map", vol=map_vol)
        self.save("t1_conf", vol=conf_vol)

    def run_ge(self):
        self._add_std()
        if not self.have_files():
            self.add(seriesdescription="molli", imagetype="MDE")
        self._filter_std()
        self.group("affinedata")
        self.select_latest()
        if self.count(nvols=1) > 0:
            self.save("t1_map")
            self.save("t1_conf")
        else:
            # GE multi volume is raw MOLLI data and needs reconstruction during processing
            LOG.info(" - No single-volume T1 map - saving raw MOLLI data from GE for subsequent reconstruction")
            self.save("t1_raw_molli")

    def run_siemens(self):
        self._add_std()
        self._filter_std()
        self.group("affinedata")
        self.select_latest()
        self.save("t1_map")
        self.save("t1_conf")

SORTERS = [
    T2(),
    T1(),
    B0(),
    B1(),
    MTR(),
    T1w(),
    T2w(),
    T2star(),
]
