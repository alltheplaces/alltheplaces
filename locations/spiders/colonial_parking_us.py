import json
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class ColonialParkingUSSpider(Spider):
    name = "colonial_parking_us"
    item_attributes = {"brand": "Colonial Parking", "brand_wikidata": "Q121494114"}
    start_urls = ["https://www.ecolonial.com/park-with-us/parking-locator/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        data = json.loads(response.xpath('//script[@id="pl-map-js-before"]/text()').re_first(r"PL_MAP_DATA = (\{.*\})"))
        for location in data["locations"]:
            item = DictParser.parse(location)
            item["branch"] = location["building"]
            item["addr_full"] = location["address"]

            oh = OpeningHours()
            for day, hours in zip(DAYS[-1:] + DAYS[:-1], location["week"]):
                if hours:
                    oh.add_range(day, *(f"{minutes // 60:02d}:{minutes % 60:02d}" for minutes in hours))
                else:
                    oh.set_closed(day)
            if oh.day_hours:
                item["opening_hours"] = oh

            apply_category(Categories.PARKING, item)
            yield item
