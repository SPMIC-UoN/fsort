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
        self.candidate_set = self.kwargs.get("candidate_set", 0)
        num_echos = self.kwargs.get("num_echos", 10)
        seriesdesc = self.kwargs.get("seriesdesc", ("t2_mapping", "t2 mapping", "t2map_resptrig", "t2map"))
        for desc in seriesdesc:
            LOG.info(f" - Looking for T2 mapping data with {num_echos} or {num_echos+1} volumes")
            self.add(seriesdescription=desc, nvols=num_echos)
            self.remove(echotime=None)
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

class ScannerT2Map(Sorter):
    """
    Scanner generated T2 map
    """
    def __init__(self, name="t2_map", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def run(self):
        """
        T2 data has multiple echos and possibly an extra T2 map to be discarded
        """
        self.candidate_set = self.kwargs.get("candidate_set", 0)
        num_echos = self.kwargs.get("num_echos", 10)
        seriesdesc = self.kwargs.get("seriesdesc", ("t2_mapping", "t2 mapping", "t2map_resptrig", "t2map"))
        found = False
        for desc in seriesdesc:
            self.add(seriesdescription=desc, nvols=num_echos+1)
            if self.have_files():
                LOG.info(f" - Found multi-echo T2 mapping data with {num_echos+1} volumes")
                self.select_latest()
                self.save("t2_map", vol=num_echos)
                found = True
                break

        if not found:
            for desc in seriesdesc:
                self.add(seriesdescription=desc, expected_number=num_echos+1, nvols=1)
                if self.have_files():
                    LOG.info(f" - Found {num_echos+1} single-volume data sets")
                    self.filter(imagetype="T2 MAP")
                    if self.have_files():
                        LOG.info(" - Found T2 MAP data")
                        self.select_latest()
                        self.save("t2_map")
                        found = True
                        break
                    else:
                        LOG.warn("No data set found with T2 MAP - ignoring")

        if not found:
            LOG.warn("No scanner T2 map found")
