import json
import re

import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.mcdonalds import McdonaldsSpider

SERVICES_MAPPING = {
    "drive": Extras.DRIVE_THROUGH,
    "wifi": Extras.WIFI,
    "mcdelivery": Extras.DELIVERY,
}


class McdonaldsRSSpider(scrapy.Spider):
    name = "mcdonalds_rs"
    item_attributes = McdonaldsSpider.item_attributes
    allowed_domains = ["www.mcdonalds.rs"]

    start_urls = ["https://www.mcdonalds.rs/restorani/"]

    def parse(self, response):
        data = response.xpath('//script[contains(., "restaurantMarkers")]/text()').get()
        match = re.search(r"var restaurantMarkers = (\[.*?\]);", data, re.DOTALL)
        pois = json.loads(match.group(1))
        for poi in pois:
            poi["street-address"] = poi.pop("address")
            item = DictParser.parse(poi)
            # TODO: parse hours
            for category in poi["categories"]:
                if match := SERVICES_MAPPING.get(category):
                    apply_yes_no(match, item, True)
            yield item
