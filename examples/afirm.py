import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class B0(Sorter):
    def __init__(self):
        Sorter.__init__(self, "b0")

    def run(self):
        self.add(seriesdescription="B0", imagetype="PHASE", nvols=1)
        self.remove(seriesdescription="pcasl")
        if self.have_files():
            self.group("echotime")
            self.select_latest()
            self.save("b0_phase_echo")
        else:
            # No phase? Look for real/imag as we can use them to reconstruct phase
            self.add(seriesdescription="B0", imagetype="REAL")
            self.remove(seriesdescription="pcasl")
            self.group("echotime")
            self.select_latest()
            self.save("b0_real_echo")
            self.clear_selection()
            self.add(seriesdescription="B0", imagetype="IMAGINARY")
            self.remove(seriesdescription="pcasl")
            self.group("echotime")
            self.select_latest()
            self.save("b0_imag_echo")

class B1(Sorter):
    def __init__(self):
        Sorter.__init__(self, "b1")
        
    def run_ge(self):
        # GE can be 1 or 2 volume data
        self.add(seriesdescription="B1", nvols=2)
        self.remove(imagetype="PHASE")
        if self.have_files():
            LOG.info("  - Found 2-volume GE data")
            self.select_vol(0)
        self.add(seriesdescription="B1", nvols=1)
        self.remove(imagetype="PHASE")
        # FIXME B1 scaling from ukat using flip angle?
        self.select_latest()
        self.save("b1")

    def run_siemens(self):
        self.add(seriesdescription="B1", nvols=1)
        self.remove(imagetype="PHASE")
        self.scale(0.1) # Siemens data is scaled by x10
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
            self.scale("PhilipsRescaleSlope", inverse=True)

        self.select_latest()
        self.save("b1")
     
class MTR(Sorter):
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
    def __init__(self):
        Sorter.__init__(self, "t2star")

    def run(self):
        self.add(seriesdescription="t2star", nvols=1)
        # FIXME remove if TE not defined
        self.remove(imagetype="PHASE")
        self.remove(imagetype="REAL")
        self.remove(imagetype="IMAGINARY")
        # FIXME ideally we want to check for T1 overlap as in renal_preproc code
        self.group("echotime")
        self.select_latest()
        self.save("t2star_e")

class T1(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t1")

    def _add_std(self):
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
        self.group("affine")
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
        self.group("affine")
        self.select_latest()
        if self.count(nvols=1) > 0:
            self.save("t1_map")
            self.save("t1_conf")
        else:
            # FIXME T1 map reconstruction for AFIRM?
            self.save("t1_map", vol=0)
            self.save("t1_conf", vol=2)

class T1w(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t1w")

    def run(self):
        self.add(seriesdescription="t1w")
        self.select_latest()
        self.save("t1w_map")

class T2w(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t2w")

    def run(self):
        self.add(seriesdescription="t2w")
        self.select_latest()
        self.save("t2w_map")

SORTERS = [
    B0(),
    B1(),
    MTR(),
    T1(),
    T1w(),
    T2w(),
    T2star(),
]
