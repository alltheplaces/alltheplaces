from datetime import datetime
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class ApoteketSESpider(Spider):
    name = "apoteket_se"
    item_attributes = {
        "brand": "Apoteket",
        "brand_wikidata": "Q1785637",
    }
    start_urls = ["https://www.apoteket.se/bff/v1/pharmacies/all"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            item = DictParser.parse(store)
            item["branch"] = store["name"].removeprefix("Apoteket ")
            item.pop("name", None)
            item["street_address"] = store["address"]
            item.pop("addr_full", None)
            item["city"] = store["region"]
            item["postcode"] = store["postalCode"]
            item["country"] = "SE"
            item["website"] = "https://www.apoteket.se" + store["url"]
            item["opening_hours"] = self.parse_hours(store["openingHours"])
            apply_category(Categories.PHARMACY, item)
            yield item

    @staticmethod
    def parse_hours(hours: list) -> str:
        oh = OpeningHours()
        for entry in hours:
            if not entry["openTime"]:
                continue
            day = DAYS[datetime.fromisoformat(entry["date"]).weekday()]
            if entry["breakStart"]:
                oh.add_range(day, entry["openTime"], entry["breakStart"])
                oh.add_range(day, entry["breakEnd"], entry["closeTime"])
            else:
                oh.add_range(day, entry["openTime"], entry["closeTime"])
        return oh.as_opening_hours()
