"""
Sorter for T2 data
"""
import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

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
        num_echos = self.kwargs.get("num_echos", 10)
        seriesdesc = self.kwargs.get("seriesdesc", ("t2_mapping", "t2 mapping", "t2map_resptrig", "t2map"))
        for desc in seriesdesc:
            self.add(seriesdescription=desc, expected_number=(num_echos, num_echos+1))
            self.remove(echotime=None)
            if self.have_files():
                break
        if not self.have_files():
            LOG.warn("No T2 mapping data found")
        if self.count() == num_echos+1:
            LOG.info(f" - {num_echos+1} echos found - trying to remove T2 MAP image")
            self.remove(imagetype="T2 MAP")
            if self.count() == num_echos+1:
                LOG.warn(f"Have {num_echos+1} echos still")

        self.save("t2_e", sort="echotime")

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

    def run(self):
        self._get_files("t2star")
        if not self.have_files():
            LOG.info("No T2star data found, checking for T2*")
            self._get_files("t2*")
        for hires_identifier in ("highres", "hires", "high_res"):
            if self.count(seriesdescription=hires_identifier) > 0:
                LOG.info(f" - Found high-res data with flag {hires_identifier}, keeping only data with this flag")
                self.filter(seriesdescription=hires_identifier)
        # FIXME ideally we want to check for T1 overlap as in renal_preproc code
        self.group("echotime", allow_none=False)
        self.select_one("seriesnumber", last=False)
        self.save("t2star_e", sort="echotime")
