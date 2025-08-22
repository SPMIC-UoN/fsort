import logging

from fsort import Sorter, run

LOG = logging.getLogger(__name__)

class RawDixon(Sorter):
    def __init__(self, includes=None, excludes=None):
        Sorter.__init__(self, "raw_dixon")
        self.dixon_includes = {
            "seriesdescription": "dixon",
        }
        self.dixon_excludes = {}
        if includes is not None:
            self.dixon_includes.update(includes)
        if excludes is not None:
            self.dixon_excludes.update(excludes)

    def _select(self, seriesnumber=None):
        self.clear_selection()
        self.add(**self.dixon_includes)
        for k, v in self.dixon_excludes.items():
            self.remove(**{k: v})
        if seriesnumber:
            self.filter(seriesnumber=seriesnumber)

    def run(self):
        self._select()
        series_numbers = [f.seriesnumber for f in self.selected]
        for idx, seriesnumber in enumerate(sorted(series_numbers)):
            self._select(seriesnumber=seriesnumber)
            LOG.info(f" - Found {len(self.selected)} files for series number {seriesnumber}")
            self.save(f"raw_dixon_series_{idx+1}")

SORTERS = [
    RawDixon(
        includes={"seriesdescription" : "mdixon-quant"},
        excludes={"imagetype" : "PHASE", "seriesdescription" : "12echoes"}
    ),
]

if __name__ == "__main__":
    run(__file__)
