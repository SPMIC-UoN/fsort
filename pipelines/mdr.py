import logging

from fsort.sorter import Sorter

LOG = logging.getLogger(__name__)

class T1(Sorter):
    def __init__(self):
        Sorter.__init__(self, "t1")

    def run(self):
        self.add(fname="t1_map_param3")
        self.select_latest()
        self.save("t1_map_mdr")
        self.clear_selection()
        self.add(fname="param3_nomdr_t1_map")
        self.select_latest()
        self.save("t1_map_nomdr")

class TKV(Sorter):
    def __init__(self):
        Sorter.__init__(self, "tkv")

    def run(self):
        self.add(fname="leftkidney")
        self.save("tkv_left")
        self.clear_selection()
        self.add(fname="rightkidney")
        self.save("tkv_right")
        self.clear_selection()
        self.add(fname="mask")
        self.filter(fname="t2w")
        self.save("tkv_mask")

class Deformation(Sorter):
    def __init__(self):
        Sorter.__init__(self, "def")

    def run(self):
        self.add(fname="jacobianmaxtranspose")
        self.save("jac_max")
        self.clear_selection()
        self.add(fname="jacobianmintranspose")
        self.save("jac_min")
        self.clear_selection()
        self.add(fname="jacobiandettranspose")
        self.save("jac")
        self.clear_selection()
        self.add(fname="deformationmaxtranspose")
        self.save("def_max")
        self.clear_selection()
        self.add(fname="deformationnormtranspose")
        self.save("def_norm")

SORTERS = [
    T1(),
    TKV(),
    Deformation(),
]
