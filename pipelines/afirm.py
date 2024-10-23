"""
FSORT config for AFIRM study
"""
import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class B0(Sorter):
    """
    B0 mapping data
    
    We need the phase at two echos. Sometimes we may not have phase data
    so save real/imaginary part if not as this can be reconstructed to phase
    """
    def __init__(self):
        Sorter.__init__(self, "b0")

    def _add_std(self, imagetype):
        self.add(seriesdescription="B0", imagetype=imagetype, nvols=1)
        self.remove(seriesdescription="pcasl")
        self.remove(seriesdescription="off-resonance")

    def run(self):
        self._add_std("PHASE")
        if self.have_files():
            self.group("echotime", allow_none=False)
            if any([len(g) > 1 for g in self.groups.values()]):
                LOG.warn(" - Could not separate B0 phase/mag data - using filename filtering")
                self.filter(fname="_ph")
                self.group("echotime", allow_none=False)
            self.select_latest()
            self.save("b0_phase_echo", sort="echotime")
        else:
            # No phase? Look for real/imag as we can use them to reconstruct phase
            LOG.info(" - No phase maps found - will look for real/imaginary parts")
            self._add_std("REAL")
            if not self.have_files():
                LOG.warn(" - No real part found")
            self.group("echotime", allow_none=False)
            self.select_latest()
            self.save("b0_real_echo", sort="echotime")
            self.clear_selection()
            self._add_std("IMAGINARY")
            if not self.have_files():
                LOG.warn(" - No imaginary part found")
            self.group("echotime", allow_none=False)
            self.select_latest()
            self.save("b0_imag_echo", sort="echotime")

class B1(Sorter):
    """
    B1 mapping data

    Quite vendor-specific
    """
    def __init__(self):
        Sorter.__init__(self, "b1")
        
    def run_ge(self):
        # GE can be 1 or 2 volume data
        self.add(seriesdescription="B1", nvols=2)
        self.remove(imagetype="PHASE")
        if self.have_files():
            LOG.info("  - Found 2-volume GE data")
        else:
            self.add(seriesdescription="B1", nvols=1)
            self.remove(imagetype="PHASE")

        # B1 scaling using flip angle?
        self.scale(factor=10, attribute="FlipAngle", inverse=True)
        self.select_latest()
        self.save("b1", vol=0)

    def run_siemens(self):
        self.add(seriesdescription="B1", nvols=1)
        self.remove(imagetype="PHASE")
        self.scale(factor=0.1) # Siemens data is scaled by x10
        if self.count(imagetype="B1") > 0:
            self.filter(imagetype="B1")
        self.select_latest()
        self.save("b1")

    def run_philips(self):
        self.add(seriesdescription="B1", nvols=1)
        self.remove(imagetype="PHASE")
        if self.count(imagetype="B1") > 0:
            self.filter(imagetype="B1")

        philips_enhanced = self.count(echonumber=3) > 0
        if philips_enhanced and self.count(echonumber=2) > 0:
            LOG.info(" - Found Philips enhanced protocol - taking echo 2")
            self.filter(echonumber=2)
        else:
            # Philips classic protocol
            self.scale(attribute="PhilipsRescaleSlope", inverse=True)

        self.select_latest()
        self.save("b1")

class MTR(Sorter):
    """
    MTR ON/OFF data
    
    This may be in separate ON/OFF files, or a single 2-volume
    file for Phillips
    """
    def __init__(self):
        Sorter.__init__(self, "mtr")

    def run(self):
        self.add(seriesdescription="MT", nvols=1)
        if self.count(seriesdescription="_ND") > 0:
            LOG.info(" - Found distcorr data, will use this in preference")
            self.filter(seriesdescription="_ND")
        self.group("seriesdescription")
        self.select_latest()
        self.save("mtr_on", seriesdescription="on")
        self.save("mtr_off", seriesdescription="off")
 
    def run_philips(self):
        self.add(seriesdescription="MT", nvols=2)
        if self.count(seriesdescription="_ND") > 0:
            LOG.info(" - Found distcorr data, will use this in preference")
            self.filter(seriesdescription="_ND")
        self.select_latest()
        self.save("mtr_on_off")

class T2star(Sorter):
    """
    T2* mapping data
    
    Need multiple echos (12 in AFIRM), real part
    """
    def __init__(self):
        Sorter.__init__(self, "t2star")

    def run(self):
        self.add(seriesdescription="t2star", nvols=1)
        self.remove(imagetype="PHASE")
        self.remove(imagetype="REAL")
        self.remove(imagetype="IMAGINARY")
        for hires_identifier in ("highres", "hires", "high_res"):
            if self.count(seriesdescription=hires_identifier) > 0:
                LOG.info(f" - Found high-res data with flag {hires_identifier}, keeping only data with this flag")
                self.filter(seriesdescription=hires_identifier)
        # FIXME ideally we want to check for T1 overlap as in renal_preproc code
        self.group("echotime", allow_none=False)
        self.select_latest()
        self.save("t2star_e", sort="echotime")

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

class T1w(Sorter):
    """
    T1w scan
    """
    
    def __init__(self):
        Sorter.__init__(self, "t1w")

    def run(self):
        self.add(seriesdescription="t1w")
        self.select_latest()
        self.save("t1w")

class T2w(Sorter):
    """
    T2w scan
    """
    
    def __init__(self):
        Sorter.__init__(self, "t2w")

    def run(self):
        self.add(seriesdescription="t2w")
        self.select_latest()
        self.save("t2w")

SORTERS = [
    B0(),
    B1(),
    MTR(),
    T1(),
    T1w(),
    T2w(),
    T2star(),
]
