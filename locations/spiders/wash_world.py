from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class WashWorldSpider(Spider):
    name = "wash_world"
    item_attributes = {"brand": "Wash World", "brand_wikidata": "Q130249954"}
    start_urls = ["https://washworld.dk/api/locations?limit=500"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json()["docs"]:
            item = DictParser.parse(location)
            item["ref"] = location["locationUid"]
            item["branch"] = item.pop("name")
            if "-" in (location.get("openHours") or ""):
                open_hour, close_hour = location["openHours"].split("-")
                item["opening_hours"] = OpeningHours()
                item["opening_hours"].add_days_range(DAYS, f"{int(open_hour):02d}:00", f"{int(close_hour):02d}:00")
            apply_category(Categories.CAR_WASH, item)
            yield item
