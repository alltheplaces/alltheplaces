import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class TheCourierGuyZASpider(scrapy.Spider):
    name = "the_courier_guy_za"
    item_attributes = {"brand": "The Courier Guy", "brand_wikidata": "Q116753262"}
    start_urls = ["https://api-pudo.co.za/api/v1/guest/lockers-data"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location.update(location.pop("detailed_address"))
            item = DictParser.parse(location)
            item["ref"] = location["code"]
            item["street_address"] = item.pop("street")
            item["branch"] = item.pop("name").replace("The Courier Guy ", "")
            item["name"] = self.item_attributes["brand"]
            item["opening_hours"] = OpeningHours()
            if location["type"]["name"] == "Locker":
                apply_category(Categories.PARCEL_LOCKER, item)
            else:
                apply_category(Categories.OFFICE_COURIER, item)
            for day_time in location["openinghours"]:
                day = day_time["day"]
                if day.strip() == "Public Holidays":
                    continue
                open_time = day_time["open_time"]
                close_time = day_time["close_time"]
                if "--" in open_time:
                    pass
                elif re.match(r"\d+:\d+:\d+", open_time):
                    item["opening_hours"].add_range(
                        day=day.strip(), open_time=open_time, close_time=close_time, time_format="%H:%M:%S"
                    )
                else:
                    item["opening_hours"].add_range(
                        day=day.strip(), open_time=open_time, close_time=close_time, time_format="%H:%M"
                    )

            yield item
