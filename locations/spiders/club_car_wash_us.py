from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ClubCarWashUSSpider(Spider):
    name = "club_car_wash_us"
    item_attributes = {"brand": "Club Car Wash", "brand_wikidata": "Q122850169"}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(url="https://clubcarwash.com/api/now/sp/page?id=locations_map")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in DictParser.get_nested_key(response.json(), "locations"):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("street")
            item["ref"] = location["sys_id"]

            if location.get("image") and location["image"] not in ("loc-def-img.png", "ccw-location-now-open-img.png"):
                item["image"] = urljoin("https://clubcarwash.com/", location["image"])

            oh = OpeningHours()
            for day_time in location["hoursOfOperation"]["items"]:
                oh.add_ranges_from_string("".join(day_time.values()))
            item["opening_hours"] = oh

            apply_category(Categories.CAR_WASH, item)

            yield item
