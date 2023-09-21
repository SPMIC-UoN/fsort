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
        self.add(fname="tkv_left_kidney")
        self.save("tkv_left")
        self.clear_selection()
        self.add(fname="tkv_right_kidney")
        self.save("tkv_right")
        self.clear_selection()
        self.add(fname="tkv_mask")
        self.save("tkv_mask")

SORTERS = [
    T1(),
    TKV(),
]
