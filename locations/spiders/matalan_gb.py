import json
from typing import Any

import scrapy
from requests import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MatalanGBSpider(scrapy.Spider):
    name = "matalan_gb"
    item_attributes = {"brand": "Matalan", "brand_wikidata": "Q12061509"}
    start_urls = ["https://www.matalan.co.uk/stores/uk"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = response.xpath('//script[@id="__NEXT_DATA__"]/text()').get()
        stores_data = json.loads(raw_data)["props"]["pageProps"]["storesData"]

        for store_data in stores_data.values():
            for store in store_data.values():
                for store_details in store:
                    item = DictParser.parse(store_details)
                    item["city"] = store_details["address"]["addressLine4"]
                    item["state"] = store_details["address"]["addressLine5"]
                    item["website"] = "/".join(
                        [
                            "https://www.matalan.co.uk/stores/uk",
                            item["state"].replace(" ", "-").lower(),
                            item["city"].replace(" ", "-").lower(),
                        ]
                    )
                    item["opening_hours"] = self.parse_opening_hours(store_details["openingTimes"])
                    yield item

    def parse_opening_hours(self, opening_times):
        opening_hours = OpeningHours()
        for day_time in opening_times:
            day = day_time["day"]
            open_time = self.format_time(day_time["openingTime"])
            close_time = self.format_time(day_time["closingTime"])
            opening_hours.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S")
        return opening_hours

    @staticmethod
    def format_time(time_str):
        return time_str if len(time_str) == 8 else time_str + ":00"
