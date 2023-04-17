import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class CircleKSpider(Spider):
    name = "circle_k"
    item_attributes = {"brand": "Circle K", "brand_wikidata": "Q3268010"}
    allowed_domains = ["www.circlek.com"]
    start_urls = ["https://www.circlek.com/stores_master.php?lat=0&lng=0&page=0"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, meta={"page": 0})

    def parse(self, response):
        if response.json()["count"] == 0:
            # crawl completed
            return

        for location_id, location in response.json()["stores"].items():
            item = DictParser.parse(location)
            item["ref"] = location_id
            item["street_address"] = item.pop("addr_full")
            item["website"] = "https://www.circlek.com" + item["website"]
            yield item

        if response.json()["count"] < 10:
            # crawl completed
            return

        next_page = response.meta["page"] + 1
        next_url = re.sub(r"\d+$", str(next_page), response.url)
        yield JsonRequest(url=next_url, meta={"page": next_page})
