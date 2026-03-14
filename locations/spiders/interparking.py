import json
import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import FormRequest

from locations.dict_parser import DictParser


class InterparkingSpider(Spider):
    name = "interparking"
    item_attributes = {"brand": "Interparking", "brand_wikidata": "Q1895863"}
    countries = ["be", "fr", "it", "nl", "pl", "ro", "es"]
    skip_auto_cc_domain = True

    async def start(self) -> AsyncIterator[FormRequest]:
        for country in self.countries:
            yield FormRequest(
                url=f"https://www.interparking.{country}/en/find-parking/search-results/?keyword=",
                formdata={"urlHash": "{}", "requestType": "FilterParkings"},
            )

    def parse(self, response, **kwargs):
        for location in json.loads(
            re.search(
                r'"carParks":(\[.*\]),\"cities',
                response.xpath('//*[contains(text(),"carParks")]/text()').get().replace("\\", ""),
            ).group(1)
        ):
            if location["brand"] == "Interparking":
                item = DictParser.parse(location)
                item["ref"] = location["externalId"]
                item["city"] = item["city"]["title"]
                item["website"] = "https://www.interparking.it/" + item["website"]
                yield item
