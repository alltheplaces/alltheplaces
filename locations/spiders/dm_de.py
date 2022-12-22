import re

from scrapy.spiders import SitemapSpider

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.structured_data_spider import StructuredDataSpider


class DrogerieMarktSpider(SitemapSpider):
    name = "dm_de"
    item_attributes = {"brand": "dm", "brand_wikidata": "Q266572"}
    sitemap_urls = ["https://store-data-service.services.dmtech.com/sitemap/DE"]
    sitemap_rules = [(r"", "parse")]
    download_delay = 0.5
    custom_settings = {
        # Looks like they try to force a login for robots.txt fetches
        "ROBOTSTXT_OBEY": False,
    }

    def sitemap_filter(self, entries):
        # Convert the sitemap entry into a query to the JSON API
        for entry in entries:
            if m := re.search(r"store\/de-([0-9]+)\/", entry["loc"]):
                entry["loc"] = f"https://store-data-service.services.dmtech.com/stores/item/de/{m.group(1)}"
                yield entry

    def parse(self, response):
        data = response.json()
        item = DictParser.parse(data)

        item["street_address"] = data["address"]["street"]
        item["street"] = None
        item["name"] = data["address"]["name"]
        item["website"] = f"https://dm.de{data['storeUrlPath']}"

        oh = OpeningHours()
        for o in data["openingHours"]:
            day_of_week = DAYS[o["weekDay"]]
            for h in o["timeRanges"]:
                oh.add_range(day_of_week, h["opening"], h["closing"])

        item["opening_hours"] = oh.as_opening_hours()

        yield item
