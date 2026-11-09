import scrapy

from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES


class KfcSGSpider(scrapy.Spider):
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

            opening_hours = " ".join(
                f"{DAYS_FROM_SUNDAY[entry['dayofweek']]} {entry['openCloseHour']}"
                for entry in location["displayOperatingHours"]["dinein"]
            )
            oh = OpeningHours()
            oh.add_ranges_from_string(opening_hours)
            item["opening_hours"] = oh

            yield item
