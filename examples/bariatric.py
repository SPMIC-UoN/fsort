import logging

from fsort import Sorter, run

LOG = logging.getLogger(__name__)

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
                # LargeFOV_LIVERmDIXON_RM       -   t2*
                # LargeFOV_LIVERmDIXON_RM_real  -   ff
                # LargeFOV_LIVERmDIXON_RMa      -   water
                # LargeFOV_LIVERmDIXON_RMb      -   fat
                self.add(fname="LargeFOV_LIVERmDIXON_RM_real", nvols=1)
                self.select_latest()
                self.save("fat_fraction")
                self.clear_selection()
                self.add(fname="LargeFOV_LIVERmDIXON_RMa", nvols=1)
                self.select_latest()
                self.save("water")
                self.clear_selection()
                self.add(fname="LargeFOV_LIVERmDIXON_RMb", nvols=1)
                self.select_latest()
                self.save("fat")
                self.clear_selection()
                self.add(fname="LargeFOV_LIVERmDIXON_RM", nvols=1)
                self.remove(fname="LargeFOV_LIVERmDIXON_RMa", nvols=1)
                self.remove(fname="LargeFOV_LIVERmDIXON_RMb", nvols=1)
                self.remove(fname="LargeFOV_LIVERmDIXON_RM_real", nvols=1)
                self.select_latest()
                self.save("t2star")

SORTERS = [
    Dixon(),
]

if __name__ == "__main__":
    run(__file__)
