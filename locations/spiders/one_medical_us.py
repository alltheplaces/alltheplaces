import json

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class OneMedicalUSSpider(scrapy.Spider):
    name = "one_medical_us"
    start_urls = ["https://www.onemedical.com/api/service_areas/"]
    item_attributes = {
        "operator": "1Life Healthcare",
        "operator_wikidata": "Q85727717",
    }

    def parse(self, response):
        for service_area in response.json():
            yield scrapy.Request(
                f"https://www.onemedical.com/api/locations/?code={service_area['code']}", callback=self.parse_locations
            )

    def parse_locations(self, response):
        service_area = json.loads(response.json())
        for location in service_area["offices"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = f"https://www.onemedical.com/locations/{service_area['code']}/{location['slug']}"
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["image"] = location["image_url"]

            oh = OpeningHours()
            oh.add_ranges_from_string(location["hours"])
            item["opening_hours"] = oh

            yield item
