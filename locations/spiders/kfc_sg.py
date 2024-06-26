import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KFCSGSpider(scrapy.Spider):
    name = "kfc_sg"
    item_attributes = KFC_SHARED_ATTRIBUTES
    start_urls = ["https://api.kfc.com.sg/stores/All/locateusStores"]

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["ref"] = location["restaurantNumber"]
            item["name"] = next((entry["value"] for entry in location["name"] if entry["lang"] == "en"), None)
            item["addr_full"] = next((entry["value"] for entry in location["address"] if entry["lang"] == "en"), None)
            item["country"] = next((entry["value"] for entry in location["country"] if entry["lang"] == "en"), None)
            item.pop("state")
            item.pop("city")

            days = {0: "Su", 1: "Mo", 2: "Tu", 3: "We", 4: "Th", 5: "Fr", 6: "Sa"}
            opening_hours = " ".join(
                f"{days[entry['dayofweek']]} {entry['openCloseHour']}"
                for entry in location["displayOperatingHours"]["dinein"]
            )
            oh = OpeningHours()
            oh.add_ranges_from_string(opening_hours)
            item["opening_hours"] = oh.as_opening_hours()

            yield item
