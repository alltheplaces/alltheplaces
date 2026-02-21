from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.dict_parser import DictParser
from locations.hours import DAYS_FROM_SUNDAY, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class NormalSpider(Spider):
    name = "normal"
    item_attributes = {"brand": "Normal", "brand_wikidata": "Q19562429"}
    start_urls = ["https://www.normal.no/stores?culture=en-150"]

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            item = DictParser.parse(location)

            item["branch"] = item.pop("name")

            address = clean_address([location.get("address"), location.get("address2")])
            item["street_address"] = address

            if location_hours := location.get("openingHours"):
                opening_hours = OpeningHours()
                for day_hours in location_hours:
                    day_index = day_hours.get("dayOfWeek")
                    if day_index is None:
                        continue

                    day = DAYS_FROM_SUNDAY[day_index]
                    if day_hours.get("closed"):
                        opening_hours.set_closed(day)
                        continue

                    opening_hours.add_range(day, day_hours.get("opens"), day_hours.get("closes"))
                if opening_hours:
                    item["opening_hours"] = opening_hours

            item["street_address"] = item.pop("addr_full", None)
            yield item
