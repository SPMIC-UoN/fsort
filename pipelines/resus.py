import logging

from fsort import Sorter, run
from fsort.sorters import SeriesDesc, ScannerT2Map, T1SERaw

LOG = logging.getLogger(__name__)

class Dixon(Sorter):
    def __init__(self):
        Sorter.__init__(self, "dixon")

    def add_dixon(self, **kwargs):
        self.add(**self.dixon_kwargs, **kwargs)
        self.remove(seriesdescription="12echoes")

    def count_dixon(self, **kwargs):
        self.add_dixon(**kwargs)
        n = self.count()
        self.clear_selection()
        return n

    def run(self):
        self.candidate_set = 0 # Use alternate dcm2niix
        self.dixon_kwargs = {
            "seriesdescription": "dixon",
            "scanningsequence": "rm",
        }
        if self.count_dixon() == 0:
            del self.dixon_kwargs["scanningsequence"]

        num_files_by_vols = {}
        for nvols in range(1, 7):
            num_files_by_vols[nvols] = self.count_dixon(nvols=nvols)
            LOG.info(f" - Found {num_files_by_vols[nvols]} {nvols}-volume mDIXON data")

        if num_files_by_vols[6] > 0:
            LOG.info(" - Found 6-volume mDIXON data")
            self.add_dixon(nvols=6)
            self.select_latest()
            self.save("water", vol=0)
            self.save("ip", vol=1)
            self.save("op", vol=2)
            self.save("fat", vol=3)
            self.save("fat_fraction", vol=4)
            self.save("t2star", vol=5)
            return

        elif num_files_by_vols[4] > 0:
            LOG.info(" - Found 4-volume mDIXON data")
            self.add_dixon(nvols=4)
            self.select_latest()
            self.save("water", vol=0)
            self.save("fat", vol=1)
            self.save("fat_fraction", vol=2)
            self.save("t2star", vol=3)
            return

        else:
            LOG.info(" - Did not find 4 or 6-volume mDIXON data, trying filename matching")
            if num_files_by_vols[1] == 6:
                LOG.info(" - Found 6 single-volume mDIXON data")
                self.add_dixon(nvols=1, fname="_real")
                self.select_latest()
                self.save("fat_fraction")
                self.clear_selection()
                self.add_dixon(nvols=1, fname="_e1")
                self.remove(fname="_e1a")           
                self.remove(fname="_e1b")                       
                self.remove(fname="_real")  
                self.select_latest()
                self.save("t2star")
                self.clear_selection()
                if self.count_dixon(nvols=1, fname="_e1a"):
                    self.add_dixon(nvols=1, fname="_e1a")
                    self.select_latest()
                    self.save("water")
                    self.clear_selection()
                    self.add_dixon(nvols=1, fname="_e2b")
                    if self.have_files():
                        self.select_latest()
                        self.save("fat")
                    else:
                        self.add_dixon(nvols=1, fname="_e1b")
                        self.select_latest()
                        self.save("fat")
                if self.count_dixon(nvols=1, fname="_e2c"):
                    self.add_dixon(nvols=1, fname="_e2c")
                    self.select_latest()
                    self.save("fat")
                    self.clear_selection()
                    self.add_dixon(nvols=1, fname="_e2")
                    self.remove(fname="_e2a")           
                    self.remove(fname="_e2b")                       
                    self.remove(fname="_real")  
                    self.select_latest()
                    self.save("water")

            elif num_files_by_vols[1] == 3 and num_files_by_vols[3] == 1:
                LOG.info(" - Found 3 single-volume / 1 3-volume mDIXON data")
                self.add_dixon(nvols=1, fname="_e1c")
                if self.have_files():
                    self.select_latest()
                    self.save("t2star")
                    self.clear_selection()
                    self.add_dixon(nvols=3)
                    self.select_latest()
                    self.save("water", vol=0)
                    self.save("fat", vol=1)
                    self.save("fat_fraction", vol=2)
                else:
                    self.add_dixon(nvols=1, fname="_e1a")
                    self.select_latest()
                    self.save("water")
                    self.clear_selection()
                    self.add_dixon(nvols=1, fname="_real")
                    self.select_latest()
                    self.save("fat_fraction")
                    self.clear_selection()
                    self.add_dixon(nvols=1, fname="_e1")
                    self.remove(fname="_e1a")                  
                    self.remove(fname=f"_real")  
                    self.select_latest()
                    self.save("t2star")
                    self.add_dixon(nvols=3)
                    self.select_latest()
                    self.save("fat", vol=2)
            elif num_files_by_vols[1] == 4 and num_files_by_vols[2] == 1:
                LOG.info(" - Found 4 single-volume / 1 2-volume mDIXON data")
                self.add_dixon(nvols=1, fname="_e1a")
                self.select_latest()
                self.save("water")
                self.clear_selection()
                self.add_dixon(nvols=1, fname="_real")
                self.select_latest()
                self.save("fat_fraction")
                self.clear_selection()
                self.add_dixon(nvols=1, fname="_e1")
                self.remove(fname="_e1a")           
                self.remove(fname="_e1b")                       
                self.remove(fname="_real")  
                self.select_latest()
                self.save("t2star")
                self.clear_selection()
                self.add_dixon(nvols=2)
                self.select_latest()
                self.save("fat", vol=1)
            else:
                LOG.warn("No usable DIXON data found")


class ADC(Sorter):
    def __init__(self):
        Sorter.__init__(self, "adc")

    def run(self):
        self.candidate_set = 1 # Use alternate dcm2niix
        self.add(fname="dwi")
        LOG.info(f" - Found {self.count()} DWI files")
        self.filter(fname="adc")
        LOG.info(f" - Found {self.count()} ADC files")
        self.select_latest()
        self.save("adc")


SORTERS = [
    Dixon(),
    SeriesDesc("t2w", seriesdesc=["cor_t2w", "t2w"]),
    SeriesDesc("ethrive", seriesdesc=["ethrive", "e-thrive"]),
    ScannerT2Map(),
    SeriesDesc("mre", seriesdesc=["swip_mrelast", "swip mrelast"]),
    SeriesDesc("mre_qiba", seriesdesc=["swip_qiba", "swip qiba"]),
    ADC(),
    T1SERaw(),
]

if __name__ == "__main__":
    run(__file__)
