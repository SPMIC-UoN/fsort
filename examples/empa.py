import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class Diffusion(Sorter):
    def __init__(self):
        Sorter.__init__(self, "diffusion")

    def run(self):
        self.add(seriesdescription="dwi")
        self.filter(seriesdescription="dir_l")
        if not self.have_files():
            self.add(seriesdescription="diff")
            self.filter(seriesdescription="RL")
            if self.count(seriesdescription="6bval_cor") > 0:
                self.filter(seriesdescription="6bval_cor")
            elif self.count(seriesdescription="b600_tra") > 0:
                self.filter(seriesdescription="b600_tra")
            elif self.count(seriesdescription="b600_cor") > 0:
                self.filter(seriesdescription="b600_cor")
            else:
                LOG.warn("No diffusion data found")
                return

        self.select_latest()
        self.save("diffusion_firstvol", vol=0)

SORTERS = [
    Diffusion(),
]
