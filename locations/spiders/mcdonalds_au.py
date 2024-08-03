import re

from scrapy import Spider

from locations.categories import Extras, apply_yes_no
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.spiders.mcdonalds import McdonaldsSpider

FACILITIES_MAPPING = {"Drive Thru": Extras.DRIVE_THROUGH, "McDelivery": Extras.DELIVERY, "WiFi": Extras.WIFI}


class McdonaldsAUSpider(Spider):
    name = "mcdonalds_au"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["mcdonalds.com.au"]
    start_urls = ["https://mcdonalds.com.au/data/store"]
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    @staticmethod
    def parse_hours(rules: list) -> OpeningHours:
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
            item = Feature(
                {
                    "city": data["store_suburb"],
                    "ref": data["store_code"],
                    "street_address": data["store_address"],
                    "phone": data.get("store_phone"),
                    "state": data["store_state"],
                    "postcode": data.get("store_postcode"),
                }
            )

            if coordinates := data.get("lat_long"):
                item["lat"] = coordinates.get("lat")
                item["lon"] = coordinates.get("lon")
            if (not item.get("lat") or not item.get("lon")) and data.get("store_geocode"):
                if m := re.search(r"(?P<lon>-?\d+(?:\.\d+))\s*,\s*(?P<lat>-?\d+(?:\.\d+))", data["store_geocode"]):
                    item["lat"] = m.group("lat")
                    item["lon"] = m.group("lon")

            item["opening_hours"] = self.parse_hours(data.get("store_trading_hour", []))

            facilities = [f.get("name") for f in data.get("store_filter", []) if f]
            for facility in facilities:
                if match := FACILITIES_MAPPING.get(facility):
                    apply_yes_no(match, item, True)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/facilities/fail/{facility}")

            yield item
