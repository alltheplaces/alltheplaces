import argparse
import json
import logging
from pathlib import Path

import requests
import requests_cache
from scrapy.commands import ScrapyCommand

from locations.name_suggestion_index import NSI_FILE_PATH, WIKIDATA_FILE_PATH

logger = logging.getLogger(__name__)


class VendorDataCommand(ScrapyCommand):

    def short_desc(self) -> str:
        return "Updated vendored data files"

    def add_options(self, parser: argparse.ArgumentParser) -> None:
        super().add_options(parser)
        parser.add_argument(
            "-w",
            "--wikidata",
            dest="wikidata_url",
            default="https://cdn.jsdelivr.net/npm/name-suggestion-index@7/dist/wikidata/wikidata.json",
            type=str,
            help="wikidata.json to be vendored [default: %(default)s]",
        )
        parser.add_argument(
            "-n",
            "--nsi",
            dest="nsi_url",
            default="https://cdn.jsdelivr.net/npm/name-suggestion-index@7/dist/json/nsi.json",
            type=str,
            help="nsi.json to be vendored [default: %(default)s]",
        )

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        with requests_cache.disabled():
            logger.info("Fetching wikidata.json")
            self._vendor_wikidata(opts)

            logger.info("Fetching nsi.json")
            self._vendor_nsi(opts)

        self._report_version(Path(NSI_FILE_PATH))
        self._report_version(Path(WIKIDATA_FILE_PATH))

    def _vendor_wikidata(self, opts: argparse.Namespace):
        wikidata = requests.get(opts.wikidata_url).json()

        for override in self._wikidata_overrides:
            override(self, wikidata)

        with open(WIKIDATA_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(wikidata, f, indent="\t", sort_keys=True)

    def _vendor_nsi(self, opts: argparse.Namespace):
        nsi = requests.get(opts.nsi_url).json()

        for override in self._nsi_overrides:
            override(self, nsi)

        with open(NSI_FILE_PATH, "w") as f:
            json.dump(nsi, f, indent="\t", sort_keys=True)

    def _report_version(self, file: Path):
        data = json.load(open(file, encoding="utf-8"))
        print(f"{file.stem.upper()} version: {data['_meta']['version']}")

    _wikidata_overrides = []
    _nsi_overrides = []
