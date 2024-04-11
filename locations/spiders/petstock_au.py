from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class PetstockAUSpider(Spider):
    name = "petstock_au"
    item_attributes = {"brand": "Petstock", "brand_wikidata": "Q106540728"}
    allowed_domains = ["connector.petstock.io"]
    start_urls = [
        "https://connector.petstock.io/api/location/?services=&distance=10000&postcode=&latitude=-23.12&longitude=132.13"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["data"]:
            item = DictParser.parse(location)
            if "Best Friends" in item["name"]:
                item["brand"] = "Best Friends"
            elif "My Pet Warehouse" in item["name"]:
                item["brand"] = "My Pet Warehouse"
            elif "FurLife" in item["name"]:
                item["brand"] = "FurLife"
            if "VET" in item["name"].upper().split():
                apply_category(Categories.VETERINARY, item)
                item["nsi_id"] = "-1"  # Skip NSI matching
            item["phone"] = location["address"]["phone"]
            item["email"] = location["address"]["email"]
            item["website"] = "https://www.petstock.com.au/pages/store/" + location["name"].lower().replace(" ", "-")
            item["opening_hours"] = OpeningHours()
            for index, hours in location["open_hours"].items():
                if len(hours) != 1:
                    continue
                day_name = list(hours)[0]
                if day_name == "Special Trading Hours":
                    continue
                elif day_name == "Today":
                    day_name = DAYS_FULL[DAYS_FULL.index(list(location["open_hours"][str(int(index) + 2)])[0]) - 2]
                elif day_name == "Tomorrow":
                    day_name = DAYS_FULL[DAYS_FULL.index(list(location["open_hours"][str(int(index) + 1)])[0]) - 1]
                if day_name not in DAYS_FULL:
                    continue
                item["opening_hours"].add_range(
                    day_name, hours[list(hours)[0]]["open"], hours[list(hours)[0]]["close"], "%H%M"
                )
            yield item
