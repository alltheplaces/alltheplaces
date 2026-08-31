import json
import re
from urllib.parse import unquote

from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.structured_data_spider import StructuredDataSpider

FIVE_GUYS_SHARED_ATTRIBUTES = {"brand": "Five Guys", "brand_wikidata": "Q1131810"}


class FiveGuysUSSpider(CrawlSpider, StructuredDataSpider):
    name = "five_guys_us"
    item_attributes = FIVE_GUYS_SHARED_ATTRIBUTES
    start_urls = ["https://restaurants.fiveguys.com/"]
    rules = [
        Rule(LinkExtractor(r"com/\w\w$")),
        Rule(LinkExtractor(r"com/\w\w/[^/]+$"), "parse"),
    ]

    def parse(self, response: TextResponse, **kwargs):
        for location in json.loads(
            unquote(
                re.search(
                    r"JSON\.parse\(decodeURIComponent\(\"(.+)\"\)\)",
                    response.xpath('//script[@type="module"]/text()').get(),
                ).group(1)
            )
        )["document"]["dm_directoryChildren"]:
            item = DictParser.parse(location)
            item["branch"] = location.get("geomodifier")
            item["website"] = "https://restaurants.fiveguys.com/{}".format(location["slug"])

            try:
                if hours := location.get("hours"):
                    item["opening_hours"] = self.parse_hours(hours)
            except Exception:
                pass

            apply_category(Categories.FAST_FOOD, item)

            yield item

    def parse_hours(self, hours: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in map(str.lower, DAYS_FULL):
            if hours[day].get("isClosed") is True:
                oh.set_closed(day)
            else:
                for time in hours[day]["openIntervals"]:
                    oh.add_range(day, time["start"], time["end"])
        return oh
