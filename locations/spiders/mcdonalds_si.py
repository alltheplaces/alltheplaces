import json
import re
from datetime import datetime

import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.mcdonalds import McdonaldsSpider


class McdonaldsSISpider(scrapy.Spider):
    name = "mcdonalds_si"
    item_attributes = McdonaldsSpider.item_attributes
    start_urls = ["https://mcdonalds.si/restavracije"]

    def parse(self, response, **kwargs):
        for location in json.loads(re.search(r"docs = (\[.+\])\.map", response.text).group(1)):
            item = DictParser.parse(location)
            item["website"] = location["slugs"]
            item["image"] = location["thumbnail"]
            item["lat"] = location["marker"]["position"]["lat"]
            item["lon"] = location["marker"]["position"]["lng"]

            apply_yes_no(Extras.DRIVE_THROUGH, item, 2 in location["features"])
            apply_yes_no(Extras.WIFI, item, 9 in location["features"])

            try:
                item["opening_hours"] = self.parse_opening_hours(location.get("hours_shop", []))
            except:
                self.logger.error(f'Error parsing opening hours: {location.get("hours_shop", [])}')

            yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if rule.get("time_from") and rule.get("time_to"):
                # Deal with mixed formats, e.g., time_from "07:00", time_to "23:00:00"
                open_time, close_time = [
                    datetime.strptime(t, "%H:%M:%S").strftime("%H:%M") if t.count(":") == 2 else t
                    for t in [rule["time_from"], rule["time_to"]]
                ]
                oh.add_range(DAYS[rule["day"] - 1], open_time, close_time)
        return oh
