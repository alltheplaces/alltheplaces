import json
import re

import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_RS, OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider
from locations.spiders.mcdonalds_cz import Categories, apply_category

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

            for category in poi["categories"]:
                if match := SERVICES_MAPPING.get(category):
                    apply_yes_no(match, item, True)

            opening_hours = re.sub(r"h<br />|H<br />|h|H", "", poi["restaurant_worktime"])
            oh = OpeningHours()
            oh.add_ranges_from_string(opening_hours, DAYS_RS)
            item["opening_hours"] = oh

            if "mccafe" in poi["categories"]:
                mccafe = item.deepcopy()
                mccafe["ref"] = "{}-mccafe".format(item["ref"])
                mccafe["brand"] = "McCafé"
                mccafe["brand_wikidata"] = "Q3114287"
                apply_category(Categories.CAFE, mccafe)
                yield mccafe

            yield item
