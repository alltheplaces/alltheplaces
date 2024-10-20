import json
import re

import scrapy

from locations.categories import Categories
from locations.dict_parser import DictParser


class SushiDailySpider(scrapy.Spider):
    name = "sushi_daily"
    start_urls = ["https://sushidaily.com/gb-en/find-us/"]
    item_attributes = {"brand": "Sushi Daily", "brand_wikidata": "Q124301611", "extras": Categories.FAST_FOOD.value}

    def parse(self, response):
        script = response.xpath('//script[contains(text(), "window.SD_KIOSKS")]/text()').re(
            r"window.SD_KIOSKS *= *(\[.*\]);"
        )[0]
        locations = json.loads(script)
        RENAME = {
            "address": "street_address",
            "gpsLongitude": "lon",
            "gpsLatitude": "lat",
        }
        # distributorGroup = supermarket brand
        EXTRA_TAGS = ["distributorGroup", "kioskType"]
        for shop in locations:
            for old, new in RENAME.items():
                shop[new] = shop.pop(old)
            shop["url"] = response.urljoin(shop["url"])
            # There are some unfixable coordinates
            if type(shop["lat"]) == str and shop["lat"].startswith("N"):
                continue
            # Some shop data contains hacks like "gpsLongitude": "10.719548,16.25z"
            for key in "lon", "lat":
                shop[key] = re.sub("[,°].*", "", shop[key])
            item = DictParser.parse(shop)
            for tag in EXTRA_TAGS:
                item["extras"][tag] = shop.pop(tag)
            yield item
