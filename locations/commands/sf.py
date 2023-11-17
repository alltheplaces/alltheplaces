import inspect
import sys

from scrapy import Spider
from scrapy.commands import BaseRunSpiderCommand
from scrapy.exceptions import UsageError

from locations.storefinders import *
from locations.user_agents import BROWSER_DEFAULT


class DetectorSpider(Spider):
    name = "detector_spider"
    start_urls = []
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT
    parameters = {
        "wikidata": None,
        "spider_key": None,
        "spider_class_name": "NewBrandZZSpider",
    }

    def parse(self, response):
        for storefinder in [cls for _, cls in inspect.getmembers(sys.modules["locations.storefinders"], inspect.isclass) if issubclass(cls, Spider)]:
            if not callable(getattr(storefinder, "storefinder_exists", None)):
                continue
            if not storefinder.storefinder_exists(response):
                continue
            new_spider = type(self.parameters["spider_class_name"], (storefinder,), {"__module__": "locations.spiders"}, response=response, wikidata=self.parameters["wikidata"], spider_key=self.parameters["spider_key"])
            if not callable(getattr(storefinder, "generate_spider_code")):
                break
            print(storefinder.generate_spider_code(new_spider))
            break

# Detect presence of a store finder at a given URL, and return a pre-filled Spider.
class SfCommand(BaseRunSpiderCommand):
    requires_project = True
    default_settings = {"LOG_LEVEL": "WARNING"}

    def syntax(self):
        return "[options] <URL to scan for store finder>"

    def short_desc(self):
        return "Detect presence of a store finder at a given URL, and return a pre-filled Spider"

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--wikidata",
            dest="wikidata",
            help="attempt to pre-fill brand name and NSI category based on supplied wikidata Q-code",
        )
        parser.add_argument(
            "--spider-key",
            dest="spider_key",
            help="pre-fill a spider key (should match the desired file name for the spider with optionally one or more _xx suffixes where xx is an ISO 3166-2 code)",
        )
        parser.add_argument(
            "--spider-class-name",
            dest="spider_class_name",
            help="pre-fill a spider class name (should be in title case and suffixed with 'Spider')",
        )

    def run(self, args, opts):
        if len(args) != 1:
            raise UsageError("Please specify single URL that is desired to be scanned for a store finder.")

        if not args[0].startswith("http"):
            raise UsageError("A http or https URL scheme is required when specifying the single URL that is desired to be scanned for a store finder.")

        if opts.wikidata:
            DetectorSpider.parameters["wikidata"] = opts.wikidata

        if opts.spider_key:
            DetectorSpider.parameters["spider_key"] = opts.spider_key

        if opts.spider_class_name:
            DetectorSpider.parameters["spider_class_name"] = opts.spider_class_name

        DetectorSpider.start_urls = [args[0]]

        crawler = self.crawler_process.create_crawler(DetectorSpider)
        self.crawler_process.crawl(crawler)
        self.crawler_process.start()
