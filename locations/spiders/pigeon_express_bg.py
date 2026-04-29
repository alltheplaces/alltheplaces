from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PigeonExpressBGSpider(Spider):
    name = "pigeon_express_bg"
    item_attributes = {"brand": "Pigeon Express", "brand_wikidata": "Q138668232"}
    start_urls = ["https://pigeonexpress.com/api/locations?locale=bg&categories=office%2Clocker"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["locations"]:
            item = DictParser.parse(location)
            item["name"] = None
            item["ref"] = location["code"]
            item["branch"] = f"{location['city']} {location['name']}"
            # 359700... is generic number for all parcel lockers
            item["phone"] = (
                f"+{location['phone']}" if location["phone"] and not location["phone"] == "35970011133" else None
            )

            oh = OpeningHours()
            for rule in location["working_hours"]:
                oh.add_range(rule["day"], rule["open"], rule["close"])
            item["opening_hours"] = oh

            if location["type"] == "office":
                apply_category(Categories.POST_OFFICE, item)
            elif location["type"] == "locker":
                apply_category(Categories.PARCEL_LOCKER, item)

            yield item
