import re

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_GR, OpeningHours


class LillyGRSpider(Spider):
    name = "lili_gr"
    item_attributes = {"brand": "Lili", "brand_wikidata": "Q111764460"}
    allowed_domains = ["lilidrogerie.gr"]
    start_urls = ["https://lilidrogerie.gr/wp-json/v1/get-store/?lang=el"]
    no_refs = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()[0]["store"]:
            item = DictParser.parse(location)
            item["addr_full"] = re.sub(r"\s+", " ", location["address"].strip())
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(location["work_time"], DAYS_GR)
            yield item
