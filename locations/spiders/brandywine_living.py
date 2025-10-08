import json
import re

import scrapy

from locations.dict_parser import DictParser


class BrandywineLivingSpider(scrapy.Spider):
    name = "brandywine_living"
    start_urls = [
        "https://www.brandycare.com/company/locations/",
    ]

    def parse(self, response, **kwargs):
        raw_data = re.search(
            r"locations\":(\[.*\])},\"locationData",
            response.xpath('//*[contains(text(),"addresscity")]/text()').get().replace("\\", ""),
        ).group(1)
        for location in json.loads(raw_data):
            item = DictParser.parse(location)
            item["ref"] = location["location"]
            item["lat"] = location["addresslatitude"]
            item["lon"] = location["addresslongitude"]
            item["branch"] = item.pop("name")
            yield item
