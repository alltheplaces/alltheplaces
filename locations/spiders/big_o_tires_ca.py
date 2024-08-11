from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class BigOTiresCASpider(Spider):
    name = "big_o_tires_ca"
    item_attributes = {"brand": "Big O Tires", "brand_wikidata": "Q4906085"}
    start_urls = ["https://wl.tireconnect.ca/api//v2/location/list?key=f5658cf9372416d9e285adb59383b55b"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        for location in response.json()["data"]["locations"]:
            item = DictParser.parse(location)
            if item["name"].startswith("Big O Tire"):
                item["branch"] = item.pop("name").removeprefix("Big O Tire").removeprefix("s").strip()
            item["street_address"] = merge_address_lines([location["address_line_1"], location["address_line_2"]])
            item["state"] = location["province_code"]

            oh = OpeningHours()
            for day, hours in location["working_hours"].items():
                open_hours = (hours["open"] or []) + (hours["break"] or [])
                open_hours.sort()
                for open_time, close_time in zip(open_hours[0::2], open_hours[1::2]):
                    oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh

            yield item
