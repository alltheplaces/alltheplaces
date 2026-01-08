import json
import re
from datetime import datetime

import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
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
            item["branch"] = item.pop("name")
            item["website"] = location["slugs"]
            item["image"] = location["thumbnail"]
            item["lat"] = location["marker"]["position"]["lat"]
            item["lon"] = location["marker"]["position"]["lng"]

            try:
                item["opening_hours"] = self.parse_opening_hours(location.get("hours_shop", []))
            except:
                self.logger.error(f'Error parsing opening hours: {location.get("hours_shop", [])}')

            # 1: delivery, 2: mcdrive, 3: parking, 4: mccafe, 5: breakfast, 6: student vouchers, 7: birthday, 8: children toys, 9: wifi
            apply_yes_no(Extras.DRIVE_THROUGH, item, 2 in location["features"])
            apply_yes_no(Extras.WIFI, item, 9 in location["features"])
            apply_yes_no(Extras.DELIVERY, item, 1 in location["features"])

            if 4 in location["features"]:
                mccafe = item.deepcopy()
                mccafe["ref"] = "{}-mccafe".format(item["ref"])
                mccafe["brand"] = "McCafé"
                mccafe["brand_wikidata"] = "Q3114287"
                apply_category(Categories.CAFE, mccafe)
                yield mccafe

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
