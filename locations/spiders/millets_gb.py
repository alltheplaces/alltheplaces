import json
from typing import Any

import scrapy
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MilletsGBSpider(scrapy.Spider):
    name = "millets_gb"
    item_attributes = {"brand": "Millets", "brand_wikidata": "Q64822903"}
    start_urls = ["https://www.millets.co.uk/pages/our-stores"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store_id in json.loads(
            response.xpath('//*[@id="app-store-locator"]//*[@type="application/json"]//text()').get()
        )["stores"]:
            yield JsonRequest(
                url=f"https://integrations-c3f9339ff060a907cbd8.o2.myshopify.dev/api/stores?fid={store_id['id']}",
                callback=self.parse_location,
            )

    def parse_location(self, response):
        if data := response.json()["stores"]:
            raw_data = data[0]
            item = DictParser.parse(raw_data)
            item["street_address"] = raw_data["address_1"]
            item["phone"] = raw_data.get("local_phone")
            item["website"] = "https://www.millets.co.uk/pages/stores/" + item["name"].lower().replace(
                " ", "-"
            ).replace("\xa0", "-")
            oh = OpeningHours()
            for day, time in raw_data["hours_sets"]["primary"]["days"].items():
                for open_close_time in time:
                    open_time = open_close_time["open"]
                    close_time = open_close_time["close"]
                    oh.add_range(day, open_time, close_time)
            item["opening_hours"] = oh

            yield item
