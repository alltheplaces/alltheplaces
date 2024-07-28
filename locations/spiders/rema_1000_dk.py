from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_NO, OpeningHours


class Rema1000DKSpider(Spider):
    name = "rema_1000_dk"
    item_attributes = {
        "brand": "REMA 1000",
        "brand_wikidata": "Q115768834",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["www.rema1000.dk"]
    start_urls = ["https://www.rema1000.dk/api/v2/stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url)

    def parse(self, response):
        for location in response.json()["data"]:
            if location.get("permanently_closed") or location.get("temporarily_closed_until"):
                continue

            item = DictParser.parse(location)
            item["website"] = location.get("store_link")

            hours_string = ""
            for day_hours in location.get("opening_hours", {}).values():
                hours_string = "{} {}: {} - {}".format(
                    hours_string, day_hours.get("day"), day_hours.get("open"), day_hours.get("close")
                )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_NO)
            item["postcode"] = str(item["postcode"])
            yield item
