import json
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class HalfordsGBSpider(scrapy.Spider):
    name = "halfords_gb"
    start_urls = ["https://www.halfords.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        raw_data = json.loads(response.xpath('//*[@type="application/json"]/text()').get())["__PRELOADED_STATE__"][
            "__reactQuery"
        ]["queries"]
        for location in raw_data:
            data = location.get("state").get("data")

            if not isinstance(data, dict):
                continue

            store_data = data.get("stores")
            if not store_data:
                continue

            for data in store_data:
                if data.get("coordinates").get("latitude") == 0:
                    continue

                item = DictParser.parse(data)
                item["street_address"] = merge_address_lines([item.pop("street_address"), data.get("address2")])
                item["website"] = "https://www.halfords.com/locations/" + data["storeDetailsLink"]

                oh = OpeningHours()
                for day_time in data["storeHours"]["workingHours"]:
                    for day, time in day_time.items():
                        for open_close_time in time:
                            if open_close_time in [{}, {"isToday": True}]:
                                continue
                            open_time = open_close_time.get("Start").strip()
                            close_time = open_close_time.get("Finish").strip()
                            oh.add_range(day=day, open_time=open_time, close_time=close_time)
                item["opening_hours"] = oh

                if data["storePrefix"] == "Halfords Autocentre":
                    item["brand_wikidata"] = "Q5641894"
                elif data["storePrefix"] == "Halfords Garage Services":
                    item["brand"] = "Halfords"
                    apply_category(Categories.SHOP_CAR_REPAIR, item)
                elif data["storePrefix"] == "National Tyres and Autocare":
                    item["brand_wikidata"] = "Q6979055"
                elif data["storePrefix"] == "Halfords Store":
                    item["brand_wikidata"] = "Q3398786"
                else:
                    item["brand_wikidata"] = "Q5641894"
                yield item
