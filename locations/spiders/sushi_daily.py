import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import set_closed


class SushiDailySpider(scrapy.Spider):
    name = "sushi_daily"
    start_urls = ["https://sushidaily.com/gb-en/find-us/"]
    item_attributes = {"brand": "Sushi Daily", "brand_wikidata": "Q124301611"}

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
        for shop in locations:
            for old, new in RENAME.items():
                shop[new] = shop.pop(old)
            shop["url"] = response.urljoin(shop["url"])
            # Some shop data contains hacks like "gpsLongitude": "10.719548,16.25z"
            for key in "lon", "lat":
                shop[key] = re.sub("[,°].*", "", shop[key])
            item = DictParser.parse(shop)

            if shop["closed"] is True:
                set_closed(item)

            item["located_in"] = shop["distributorGroup"]
            item["extras"]["kioskType"] = str(shop["kioskType"])

            apply_category(Categories.FAST_FOOD, item)

            yield item
