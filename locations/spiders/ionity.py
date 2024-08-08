import re

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class IonitySpider(Spider):
    name = "ionity"
    item_attributes = {"brand": "Ionity", "brand_wikidata": "Q42717773"}
    start_urls = ["https://ionity.eu/location.json"]
    no_refs = True

    def parse(self, response, **kwargs):
        for location in response.json()["locations"]:
            if location["status"] == "0":
                continue  # Under construction

            item = DictParser.parse(location)

            item["street_address"] = location["adress"]
            item["postcode"] = location["plz"]

            if "Station open 24/7" in location["description"]:
                item["opening_hours"] = "24/7"

            if m := re.search(r"Number of CCS Chargers: (\d+)", location["description"]):
                item["extras"]["socket:CCS"] = m.group(1)
            apply_category(Categories.CHARGING_STATION, item)
            yield item
