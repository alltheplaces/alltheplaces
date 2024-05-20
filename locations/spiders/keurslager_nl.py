from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class KeurslagerNLSpider(Spider):
    name = "keurslager_nl"
    item_attributes = {"brand": "Keurslager", "brand_wikidata": "Q114637402"}
    start_urls = ["https://www.keurslager.nl/map-locations?hubId=41"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for ref, location in response.json().items():
            if not isinstance(location, dict):
                continue
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["ref"] = ref
            item["extras"]["ref:google"] = location["placeid"]

            item["opening_hours"] = OpeningHours()
            for rule in location["openTimes"]:
                if rule["closed"]:
                    continue
                item["opening_hours"].add_range(DAYS[rule["day"]], rule["openTime"], rule["closeTime"])

            yield item
