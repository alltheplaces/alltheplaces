import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class CrashChampionsUSSpider(Spider):
    name = "crash_champions_us"
    item_attributes = {"brand": "Crash Champions", "brand_wikidata": "Q121435028"}
    start_urls = ["https://www.crashchampions.com/locations?view=view-all-centers"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(
            re.search(
                r"geoPoints\"\s*:\s*(\[.*\]),\"user\"", response.xpath('//*[contains(text(),"geoPoints")]/text()').get()
            ).group(1)
        )
        for location in raw_data:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("CRASH CHAMPIONS ")
            item["street_address"] = item.pop("addr_full")
            item["ref"] = location["nid"]
            item["website"] = response.urljoin(location["alias"])
            oh = OpeningHours()
            for day_time in location.keys():
                if "openhours" in day_time:
                    day_time_string = location[day_time]
                    oh.add_ranges_from_string(day_time_string)
            item["opening_hours"] = oh

            if "Formerly Service King Collision" in location["former_sk_shop"]:
                item["extras"]["old_name"] = "Service King"

            apply_category(Categories.SHOP_CAR_REPAIR, item)

            yield item
