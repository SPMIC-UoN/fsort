import logging

from fsort.sorter import Sorter

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
