import logging

from fsort import Sorter, run

LOG = logging.getLogger(__name__)

from afirm import B0

class B1(Sorter):
    """
    B1 mapping data

    Unfortunately have to do filename matching to remove phase images...
    """
    def __init__(self):
        Sorter.__init__(self, "b1")

    def run_philips(self):
        self.add(seriesdescription="B1", nvols=4)
        if self.have_files():
            self.select_latest()
            self.save("b1", vol=2)
        else:
            self.add(seriesdescription="B1", echonumber=2, nvols=1)
            self.remove(fname="_ph")
            self.select_latest()
            self.save("b1")

class Dixon(Sorter):
    def __init__(self):
        Sorter.__init__(self, "dixon")

    def run(self):
        self.add(seriesdescription="livermdixon", nvols=4)
        self.remove(seriesdescription="coronal")
        self.remove(seriesdescription="sagital")
        if self.have_files():
            self.select_latest()
            if self.count(imagetype="ff"):
                # Special case, different order
                self.save("t2star", vol=0)
                self.save("water", vol=1)
                self.save("fat", vol=2)
                self.save("fat_fraction", vol=3)
            else:
                self.save("water", vol=0)
                self.save("fat", vol=1)
                self.save("fat_fraction", vol=2)
                self.save("t2star", vol=3)
        else:
            self.add(seriesdescription="livermdixon", nvols=3)
            self.remove(seriesdescription="coronal")
            self.remove(seriesdescription="sagital")
            if self.have_files():
                self.select_latest()
                self.save("water", vol=0)
                self.save("fat", vol=1)
                self.save("fat_fraction", vol=2)
                self.clear_selection()
                self.add(seriesdescription="livermdixon", nvols=1)
                self.remove(seriesdescription="coronal")
                self.remove(seriesdescription="sagital")
                if self.have_files():
                    self.select_latest()
                    self.save("t2star")
            else:
                # Special case for 4 separate files in BARI_05_V4
                # LIVERmDIXON_RM       -   t2*
                # LIVERmDIXON_RM_real  -   ff
                # LIVERmDIXON_RMa      -   water
                # LIVERmDIXON_RMb      -   fat
                self.add(fname="LIVERmDIXON_RM_real", nvols=1)
                self.select_latest()
                self.save("fat_fraction")
                self.clear_selection()
                self.add(fname="LIVERmDIXON_RMa", nvols=1)
                self.select_latest()
                self.save("water")
                self.clear_selection()
                self.add(fname="LIVERmDIXON_RMb", nvols=1)
                self.select_latest()
                self.save("fat")
                self.clear_selection()
                # Sometimes water/fat in one file
                self.add(fname="LIVERmDIXON_RMa", nvols=2)
                self.select_latest()
                self.save("water", vol=0)
                self.save("fat", vol=1)
                self.clear_selection()
                self.add(fname="LIVERmDIXON_RM", nvols=1)
                import string
                for letter in string.ascii_lowercase:
                    # Don't want anything with a letter suffix, just the first
                    self.remove(fname=f"LIVERmDIXON_RM{letter}", nvols=1)
                self.remove(fname="LIVERmDIXON_RM_real", nvols=1)
                self.select_latest()
                self.save("t2star")

class MolliLiver(Sorter):
    def __init__(self):
        Sorter.__init__(self, "molli_liver")

    def run(self):
        self.add(seriesdescription="lms_molli_standard", nvols=10)
        if "BARI_003_V1" in self._outdir:
            LOG.info(" - Special case for BARI_003_V1 - ignoring 10 volume data will take e2 instead")
            self.clear_selection()
        if self.have_files():
            self.select_latest()
            self.save("t1_map", vol=8)
            self.save("t1_conf", vol=9)
        else:
            self.add(seriesdescription="lms_molli_standard", echonumber=2, nvols=2)
            self.select_latest()
            self.save("t1_map", vol=0)
            self.save("t1_conf", vol=1)

class MolliKidney(Sorter):
    def __init__(self):
        Sorter.__init__(self, "molli_kidney")

    def run(self):
        self.add(seriesdescription="kidney_cor_t1_molli", nvols=10)
        if self.have_files():
            self.select_latest()
            self.save("t1_map", vol=8)
            self.save("t1_conf", vol=9)
        else:
            self.add(seriesdescription="kidney_cor_t1_molli", echonumber=2, nvols=2)
            self.select_latest()
            self.scale(attribute="PhilipsRWVSlope", inverse=True)
            self.save("t1_map", vol=0)
            self.save("t1_conf", vol=1)

class EThrive(Sorter):
    def __init__(self):
        Sorter.__init__(self, "ethrive")

    def run(self):
        self.add(seriesdescription="e-thrive")
        self.select_latest()
        self.save("ethrive")

class T2(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t2")

    def run(self):
        self.add(seriesdescription="t2_mapping", nvols=11)
        if self.have_files():
            self.select_latest()
            self.save("t2", vol=10)
        elif "BARMRI_03_V2" in self._outdir:
            LOG.info(" - Special case for BARMRI_03_V2 - taking e1 instead of e2")
            self.add(seriesdescription="t2_mapping", imagetype="map", echonumber=1, nvols=1)
            self.select_latest()
            self.save("t2")
        else:
            self.add(seriesdescription="t2_mapping", echonumber=2, nvols=1)
            self.select_latest()
            self.save("t2")

SORTERS = [
    B0(),
    B1(),
    Dixon(),
    MolliLiver(),
    MolliKidney(),
    EThrive(),
    T2(),
]

if __name__ == "__main__":
    run(__file__)
