from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class BigLotsUSSpider(Spider):
    name = "big_lots_us"
    item_attributes = {"brand": "Big Lots", "brand_wikidata": "Q4905973"}
    start_urls = [
        "https://core.service.elfsight.com/p/boot/?page=https%3A%2F%2Fbiglots.com%2Fstore-locator%2F&w=38636f5f-4115-4585-8c00-9e245fd92818"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["widgets"]["38636f5f-4115-4585-8c00-9e245fd92818"]["data"]["settings"][
            "locations"
        ]:
            location.update(location.pop("place"))
            item = DictParser.parse(location)
            item["website"] = item["name"] = None

            item["image"] = location["photo"]["url"]
            item["extras"]["ref:google:place_id"] = location["placeId"]

            item["opening_hours"] = self.parse_opening_hours(location)

            yield item

    def parse_opening_hours(self, location: dict) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            if location["day{}Open".format(day)] is False:
                oh.set_closed(day)
                continue
            for rule in location["day{}Hours".format(day)]:
                oh.add_range(day, rule["timeRange"][0], rule["timeRange"][1])

        return oh
