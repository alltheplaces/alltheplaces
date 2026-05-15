import json
import re
from typing import Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class FloorworldAUSpider(Spider):
    name = "floorworld_au"
    item_attributes = {"brand": "Floorworld", "brand_wikidata": "Q117156913"}
    allowed_domains = ["floorworld.com.au"]
    start_urls = ["https://floorworld.com.au/find-a-store/"]

    def parse(self, response: Response) -> Iterable[dict]:
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "var markers =")]/text()').get()
        ).values():
            item = DictParser.parse(location)

            item["street_address"] = item.pop("addr_full", None)
            item["website"] = location.get("permalink")
            item["branch"] = re.sub(r"(?i)\s*Floorworld\s*", " ", item.pop("name", None)).strip()

            if hours_raw := location.get("hours"):
                oh = OpeningHours()
                for rule in json.loads(hours_raw):
                    if rule.get("status") == "open" and rule.get("start") and rule.get("end"):
                        oh.add_range(
                            day=rule["day"], open_time=rule["start"], close_time=rule["end"], time_format="%I:%M %p"
                        )

                if oh:
                    item["opening_hours"] = oh

            yield item
