import json
import os
import pathlib
import pprint

from scrapy.commands import BaseRunSpiderCommand
from scrapy.exceptions import UsageError

from locations.hours import OpeningHours
from locations.microdata_parser import MicrodataParser
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class MySpider(StructuredDataSpider):
    name = "my_spider"
    start_urls = None
    item_attributes = {}
    user_agent = BROWSER_DEFAULT
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        items = MicrodataParser.extract_microdata(response)
        self.logger.debug("Microdata %s", json.dumps(items, indent=2))
        yield from self.parse_sd(response)

    def pre_process_data(self, ld_data, **kwargs):
        self.logger.debug("JSON-LD %s", json.dumps(ld_data, indent=2))

    def post_process_item(self, item, response, ld_data, **kwargs):
        if isinstance(item.get("opening_hours"), OpeningHours):
            item["opening_hours"] = item["opening_hours"].as_opening_hours()

        print(item)
        yield item


# See what ATP libraries can do with a given web site / web page.
class SdCommand(BaseRunSpiderCommand):
    requires_project = True
    default_settings = {"LOG_LEVEL": "WARNING"}

    def syntax(self):
        return "[options] <file or URL to decode>"

    def short_desc(self):
        return "Decode a web page or file for structured data with ATP scrapy library code"

    def add_options(self, parser):
        super().add_options(parser)
        parser.add_argument(
            "--wanted-types",
            dest="wanted_types",
            help="wanted place type(s), many times not required as defaults cope with most",
        )
        parser.add_argument(
            "--wikidata",
            dest="wikidata",
            help="wikidata Q-code, see if brand name and NSI category data pulled in",
        )
        parser.add_argument(
            "--spider-name",
            dest="spider_name",
            help="specify spider name, possibly to see result of pipeline country inference",
        )
        parser.add_argument(
            "--stats",
            action="store_true",
            help="show crawl counters",
        )

    def run(self, args, opts):
        if len(args) != 1:
            raise UsageError("Please specify single file or URL to load")

        if args[0].startswith("http"):
            MySpider.start_urls = [args[0]]
        else:
            path = os.path.abspath(args[0])
            MySpider.start_urls = [pathlib.Path(path).as_uri()]

        if opts.wikidata:
            MySpider.item_attributes["brand_wikidata"] = opts.wikidata

        if opts.spider_name:
            MySpider.name = opts.spider_name

        if opts.wanted_types:
            MySpider.wanted_types = opts.wanted_types.split(",")

        crawler = self.crawler_process.create_crawler(MySpider, **opts.spargs)
        self.crawler_process.crawl(crawler)
        self.crawler_process.start()
        stats_dict = crawler.stats.get_stats()
        if stats_dict.get("item_scraped_count", 0) == 0:
            print("failed to decode structured data")
        if opts.stats:
            pprint.pprint(stats_dict)
