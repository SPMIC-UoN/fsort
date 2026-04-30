import logging

from fsort import Sorter, run
from fsort.sorters import SeriesDesc, ScannerT2Map, T1SERaw, T2, MTR

LOG = logging.getLogger(__name__)

class DTIPhaseEncoding(Sorter):
    """
    Sorts DTI series by phase encoding direction and assigns names like dti_pa, dti_ap, dti_lr, dti_rl.
    """
    def __init__(self, name="dti", name_template="dti_{pe_dir}", **kwargs):
        Sorter.__init__(self, name, **kwargs)

    def run(self):
        pedirs = {
            "j-" : "ap",
            "j" : "pa",
            "i-" : "rl",
            "i" : "lr",
        }
        for pedir, label in pedirs.items():
            self.add(seriesdescription="DTI", phaseencodingdirection=pedir, match_type=self.EXACT)
            if self.have_files():
                LOG.info(f" - Found DTI data with phase encoding {label}")
                self.select_latest()
                self.save("dti_" + label)
                self.clear_selection()
            else:
                self.add(seriesdescription="DTI")
                self.filter(seriesdescription=label)
                if self.have_files():
                    LOG.info(f" - Found DTI data with phase encoding {label} using series description")
                    self.select_latest()
                    self.save("dti_" + label)
                    self.clear_selection()
                else:
                    LOG.info(f" - No DTI data found with phase encoding {label}")


SORTERS = [
    SeriesDesc("mprage", seriesdesc=["MPRAGE"]),
    SeriesDesc("flair", seriesdesc=["FLAIR"]),
    DTIPhaseEncoding(),
]

if __name__ == "__main__":
    run(__file__)
