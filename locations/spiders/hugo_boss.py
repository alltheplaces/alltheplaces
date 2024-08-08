import json

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Clothes, apply_clothes
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class HugoBossSpider(Spider):
    name = "hugo_boss"
    item_attributes = {"brand": "Hugo Boss", "brand_wikidata": "Q491627"}
    allowed_domains = ["api.hugoboss.eu"]
    start_urls = [
        "https://api.hugoboss.eu/s/UK/dw/shop/v22_10/stores?client_id=871c988f-3549-4d76-b200-8e33df5b45ba&latitude=53.6912856662977&longitude=-2.0727839000000072&count=200&maxDistance=100000000&distanceUnit=mi&start=0"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            item["website"] = "https://www.hugoboss.com/us/storedetail?storeid=" + location["id"]
            item["email"] = location.get("c_ContactEmail")

            if location.get("store_hours"):
                opening_hours = json.loads(location["store_hours"])
                item["opening_hours"] = OpeningHours()
                for day_number, day_hours in opening_hours.items():
                    if type(day_hours[0]) is list:
                        for day_hours_period in day_hours:
                            item["opening_hours"].add_range(
                                DAYS[int(day_number) - 1], day_hours_period[0], day_hours_period[1]
                            )
                    else:
                        item["opening_hours"].add_range(DAYS[int(day_number) - 1], day_hours[0], day_hours[1])

            if "womenswear" in location.get("c_categories", []):
                apply_clothes([Clothes.WOMEN], item)
            if "menswear" in location.get("c_categories", []):
                apply_clothes([Clothes.MEN], item)
            if "kidswear" in location.get("c_categories", []):
                apply_clothes([Clothes.CHILDREN], item)

            yield item

        if response.json().get("next"):
            yield JsonRequest(url=response.json()["next"], callback=self.parse)
