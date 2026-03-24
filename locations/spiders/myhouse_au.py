from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class MyhouseAUSpider(Spider):
    name = "myhouse_au"
    item_attributes = {
        "brand": "MyHouse",
        "brand_wikidata": "Q28854270",
        "extras": {"shop": "houseware"},
    }
    allowed_domains = ["myhouse.com.au"]
    start_urls = ["https://myhouse.com.au/api/get-stores"]

    async def start(self) -> AsyncIterator[Request]:
        for url in self.start_urls:
            yield Request(url=url, method="POST")

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["geometry"] = location["location"]
            item["street_address"] = clean_address([location["address1"], location["address2"]])
            item["website"] = "https://myhouse.com.au/stores/" + location["slug"]
            item["opening_hours"] = OpeningHours()
            for day_name, day_hours in location["storeHours"].items():
                item["opening_hours"].add_range(day_name.title(), day_hours["open"], day_hours["close"])
            yield item
