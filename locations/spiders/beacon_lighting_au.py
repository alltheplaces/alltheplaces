from json import loads
from urllib.parse import quote

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BeaconLightingAUSpider(Spider):
    name = "beacon_lighting_au"
    item_attributes = {
        "brand": "Beacon Lighting",
        "brand_wikidata": "Q109626941",
        "extras": Categories.SHOP_LIGHTING.value,
    }
    allowed_domains = ["www.beaconlighting.com.au"]
    start_urls = ["https://www.beaconlighting.com.au/beaconlocator/index/ajax/"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["items"]:
            item = DictParser.parse(location)
            item["ref"] = str(location["id"])
            item["street_address"] = item.pop("addr_full")
            item["state"] = location["state_data"]["code"]
            item["image"] = location["location_image"]
            item["website"] = "https://www.beaconlighting.com.au/storelocator/" + quote(location["url_key"]) + "/"

            item["opening_hours"] = OpeningHours()
            schedule_dict = loads(location["schedule_string"])
            for day_name, day_details in schedule_dict.items():
                if day_details[f"{day_name}_status"] != "1":
                    continue
                open_time_1 = day_details["from"]["hours"] + ":" + day_details["from"]["minutes"]
                close_time_1 = day_details["break_to"]["hours"] + ":" + day_details["break_to"]["minutes"]
                open_time_2 = day_details["break_from"]["hours"] + ":" + day_details["break_from"]["minutes"]
                close_time_2 = day_details["to"]["hours"] + ":" + day_details["to"]["minutes"]
                if close_time_1 == "00:00" and open_time_2 == "00:00":
                    item["opening_hours"].add_range(day_name.title(), open_time_1, close_time_2)
                else:
                    item["opening_hours"].add_range(day_name.title(), open_time_1, close_time_1)
                    item["opening_hours"].add_range(day_name.title(), open_time_2, close_time_2)

            yield item
