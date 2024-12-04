from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class WoolworthsNZSpider(Spider):
    name = "woolworths_nz"
    METRO = {"brand": "Woolworths Metro", "brand_wikidata": "Q123699264"}
    item_attributes = {"brand": "Woolworths", "brand_wikidata": "Q5176845", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["api.cdx.nz"]
    start_urls = ["https://api.cdx.nz/site-location/api/v1/sites?latitude=-42&longitude=174&maxResults=10000"]
    user_agent = BROWSER_DEFAULT
    requires_proxy = "NZ"

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["siteDetail"]:
            item = DictParser.parse(location["site"])
            if item["name"].startswith("Metro "):
                item["brand"] = self.METRO["brand"]
                item["brand_wikidata"] = self.METRO["brand_wikidata"]
            item.pop("state", None)
            if location["site"].get("email") == "null":
                item.pop("email", None)
            item["website"] = (
                "https://www.woolworths.co.nz/store-finder/"
                + str(item["ref"])
                + "/"
                + item["city"].lower().replace(" ", "-").replace(",", "")
                + "/"
                + item["name"].lower().replace(" ", "-").replace(",", "")
            )
            item["opening_hours"] = OpeningHours()
            for day_name in DAYS_FULL:
                if not location["tradingHours"][0].get(day_name.lower()):
                    continue
                item["opening_hours"].add_range(
                    day_name,
                    location["tradingHours"][0].get(day_name.lower())["startTime"],
                    location["tradingHours"][0].get(day_name.lower())["endTime"],
                    "%H:%M:%S",
                )
            yield item
