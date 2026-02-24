import argparse
import os
import pathlib
import pprint
from typing import Iterable

from scrapy.commands import BaseRunSpiderCommand
from scrapy.exceptions import UsageError
from scrapy.http import Response

from locations.items import Feature
from locations.open_graph_spider import OpenGraphSpider
from locations.user_agents import BROWSER_DEFAULT


class MySpider(OpenGraphSpider):
    name = "my_spider"
    start_urls = None
    item_attributes = {}
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def post_process_item(self, item, response: Response, **kwargs) -> Iterable[Feature]:
        print(item)
        yield item


# See what ATP libraries can do with a given web site / web page.
class OgCommand(BaseRunSpiderCommand):
    requires_project = True
    default_settings = {"LOG_LEVEL": "WARNING"}

    def syntax(self) -> str:
        return "[options] <file or URL to decode>"

    def short_desc(self) -> str:
        return "Decode a web page or file for opengraph with ATP scrapy library code"

    def add_options(self, parser: argparse.ArgumentParser) -> None:
        super().add_options(parser)
        parser.add_argument(
            "--wanted-types",
            dest="wanted_types",
            help="wanted place type(s). Optionally specify ie: place,business.business,store,article,website",
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

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        if len(args) != 1:
            raise UsageError("Please specify single file or URL to load")

        if args[0].startswith("http"):
            MySpider.start_urls = [args[0]]
        else:
            path = os.path.abspath(args[0])
            MySpider.start_urls = [pathlib.Path(path).as_uri()]

        if opts.wanted_types:
            MySpider.wanted_types = opts.wanted_types.split(",")

        if opts.wikidata:
            MySpider.item_attributes["brand_wikidata"] = opts.wikidata

        if opts.spider_name:
            MySpider.name = opts.spider_name

        if crawler_process := self.crawler_process:
            crawler = crawler_process.create_crawler(MySpider, **opts.spargs)
            crawler_process.crawl(crawler)
            crawler_process.start()
            if crawler.stats:
                stats_dict = crawler.stats.get_stats()
                if stats_dict.get("item_scraped_count", 0) == 0:
                    print("failed to decode open graph data")
                if opts.stats:
                    pprint.pprint(stats_dict)
            else:
                raise RuntimeError("Statistics collector not defined for crawler process")
        else:
            raise RuntimeError("Crawler process not defined")
