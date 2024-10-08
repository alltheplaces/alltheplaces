import json
import re

import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsSISpider(scrapy.Spider):
    name = "mcdonalds_si"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://www.mcdonalds.si/restavracije/"]

    def parse(self, response, **kwargs):
        for location in json.loads(re.search(r"docs = (\[.+\])\.map", response.text).group(1)):
            item = DictParser.parse(location)
            item["website"] = location["slugs"]
            item["image"] = location["thumbnail"]
            item["lat"] = location["marker"]["position"]["lat"]
            item["lon"] = location["marker"]["position"]["lng"]

            apply_yes_no(Extras.DRIVE_THROUGH, item, 2 in location["features"])
            apply_yes_no(Extras.WIFI, item, 9 in location["features"])

            item["opening_hours"] = OpeningHours()
            for rule in location["hours_shop"]:
                item["opening_hours"].add_range(DAYS[rule["day"] - 1], rule["time_from"], rule["time_to"])

            yield item
