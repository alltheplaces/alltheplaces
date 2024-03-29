import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ShopwisePHSpider(Spider):
    name = "shopwise_ph"
    item_attributes = {"brand": "Shopwise", "brand_wikidata": "Q118674375", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["api.shopwise.com.ph"]
    start_urls = ["https://api.shopwise.com.ph/api/web/our-stores?site_id=2"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["branches"]:
            if not location.get("enabled"):
                continue
            item = DictParser.parse(location)
            item["phone"] = re.sub(
                r"<[^>]+>", "", location["phone"].split(" loc", 1)[0].split(";", 1)[0].split("/", 1)[0]
            )
            ph_regions = {
                region["id"]: re.sub(r"^Region [\w\-]+ \(([^\)]+)\)$", r"\1", region["name"]).title()
                for region in response.json()["perRegions"]
            }
            item["state"] = ph_regions[location["region_id"]]
            hours_string = "Mo-Su: " + re.sub(r"<[^>]+>", "", location.get("store_hours", ""))
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)
            yield item
