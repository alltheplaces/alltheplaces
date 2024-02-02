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
    (e.g. vodafone_de and vodafone_it).
    """

    requires_project = True
    default_settings = {"LOG_ENABLED": True}

    def short_desc(self):
        return "Look for wikidata code duplication across spiders"

    def add_options(self, parser):
        ScrapyCommand.add_options(self, parser)

    @staticmethod
    def spider_properties(name):
        spider = find_spider_class(name)
        filename = sys.modules[spider.__module__].__file__
        filename = filename.replace(".pyc", ".py")
        filename = os.path.relpath(filename)
        wikidata_codes = set()
        with open(filename) as f:
            for line in f.readlines():
                codes = re.findall("[\"|'](Q[0-9]*)[\"|']", line)
                for code in codes:
                    wikidata_codes.add(code)
        return {"name": name, "filename": filename, "wikidata_codes": wikidata_codes}

    def run(self, args, opts):
        codes = dict()
        for spider_name in self.crawler_process.spider_loader.list():
            props = self.spider_properties(spider_name)
            for code in props["wikidata_codes"]:
                code_spiders = codes.get(code, set())
                code_spiders.add(props["filename"])
                codes[code] = code_spiders

        # Now look for wikidata codes appearing in multiple spiders.
        for code, code_spiders in codes.items():
            if len(code_spiders) > 1:
                logger.info("%s -> %s", code, code_spiders)
