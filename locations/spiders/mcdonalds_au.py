import re

from scrapy import Spider

from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.spiders.mcdonalds import McDonaldsSpider


class McDonaldsAUSpider(Spider):
    name = "mcdonalds_au"
    item_attributes = McDonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.com.au"]
    start_urls = ["https://mcdonalds.com.au/data/store"]

    @staticmethod
    def parse_hours(rules: []) -> OpeningHours:
        oh = OpeningHours()
        for day, start_time, end_time in rules:
            day = sanitise_day(day)
            if not day:
                continue
            if start_time == "9999" or end_time == "9999":
                continue
            if end_time == "2400":
                end_time = "2359"
            if start_time and end_time:
                try:
                    oh.add_range(day, start_time, end_time, time_format="%H%M")
                except:
                    pass
        return oh

    def parse(self, response):
        for data in response.json():
            properties = {
                "city": data["store_suburb"],
                "ref": data["store_code"],
                "street_address": data["store_address"],
                "phone": data.get("store_phone"),
                "state": data["store_state"],
                "postcode": data.get("store_postcode"),
            }

            if data.get("lat_long"):
                properties["lat"] = data["lat_long"].get("lat")
                properties["lon"] = data["lat_long"].get("lon")
            if (not properties.get("lat") or not properties.get("lon")) and data.get("store_geocode"):
                if m := re.search(r"(?P<lon>-?\d+(?:\.\d+))\s*,\s*(?P<lat>-?\d+(?:\.\d+))", data["store_geocode"]):
                    properties["lat"] = m.group("lat")
                    properties["lon"] = m.group("lon")

            properties["opening_hours"] = self.parse_hours(data.get("store_trading_hour", []))

            yield Feature(**properties)
