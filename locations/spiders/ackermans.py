import json
import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class AckermansSpider(scrapy.Spider):
    name = "ackermans"
    item_attributes = {
        "brand": "Ackermans",
        "brand_wikidata": "Q4674255",
    }
    start_urls = ["https://www.ackermans.co.za/pages/store-directory"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        authorization_token = re.search(r"Authorization\s*:\s*\"([A-Za-z0-9\s]+)\"", response.text).group(1)
        yield scrapy.Request(
            url="https://ackermans.commercebridge.tech/rest/v1/store/locator",
            headers={"authorization": authorization_token},
            callback=self.parse_details,
        )

    def parse_details(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item["website"] = "https://www.ackermans.co.za/pages/store-details?storeId=" + str(item["ref"])
            item["opening_hours"] = OpeningHours()
            for key, value in json.loads(store.get("openingHours")).items():
                day = key
                open_time = value["open"]
                close_time = value["close"]
                item["opening_hours"].add_range(day, open_time, close_time, "%H:%M:%S")
            yield item
