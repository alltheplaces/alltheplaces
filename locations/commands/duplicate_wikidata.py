import json
import logging
import os
import re
import sys

from scrapy.commands import ScrapyCommand

from locations.exporters.geojson import find_spider_class

logger = logging.getLogger(__name__)


class DuplicateWikidataCommand(ScrapyCommand):
    """
    Look for the same wikidata code appearing in multiple spider files. In many cases
    this provides the nudge for the attribute value to be shared between spiders
    where the duplication is very simple i.e. the same brand in multiple countries
    (e.g. vodafone_de and vodafone_it). In other cases it can show that duplicate
    spiders have crept into the code base!
    """

    requires_project = True
    default_settings = {"LOG_ENABLED": True}

    def short_desc(self):
        return "Report instances of the same wikidata code in multiple spider files"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)
        parser.add_argument(
            "--outfile",
            dest="outfile",
            metavar="OUTFILE",
            help="write output to file in JSON format",
        )
        parser.add_argument(
            "--cross-directory",
            dest="cross_directory",
            action="store_true",
            help="only report duplicate wikidata codes if from multiple spider directories",
        )

    @staticmethod
    def wikidata_spiders(crawler_process):
        codes = {}
        for spider_name in crawler_process.spider_loader.list():
            spider = find_spider_class(spider_name)
            file_name = sys.modules[spider.__module__].__file__
            simple_name = file_name.split("/locations/")[-1]
            with open(file_name) as f:
                for code in re.findall("[\"|'](Q[0-9]*)[\"|']", f.read()):
                    files = codes.get(code, set())
                    files.add(simple_name)
                    codes[code] = files
        return codes

    def run(self, args, opts):
        duplicates = {}
        codes = self.wikidata_spiders(self.crawler_process)
        for code, files in codes.items():
            if len(files) == 1:
                # wikidata codes that come from one spider only are not interesting to report
                continue
            if opts.cross_directory:
                unique_dirs = set()
                for file in files:
                    unique_dirs.add(os.path.dirname(file))
                if len(unique_dirs) == 1:
                    # duplicates all exist in the same spider directory, ignore given command line option
                    continue
            duplicates[code] = list(files)

        # The results either go to terminal or a JSON file
        if opts.outfile:
            with open(opts.outfile, "w") as f:
                json.dump(duplicates, f)
        else:
            for code, files in duplicates.items():
                print(code + " -> " + str(files))
