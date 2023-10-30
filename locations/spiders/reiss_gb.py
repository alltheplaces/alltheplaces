import re

from scrapy import Request
from scrapy.http import JsonRequest
from scrapy.spiders import SitemapSpider

from locations.spiders.johnlewis import JohnLewisSpider
from locations.structured_data_spider import StructuredDataSpider


class ReissGBSpider(StructuredDataSpider):
    name = "reiss_gb"
    item_attributes = {"brand": "Reiss", "brand_wikidata": "Q7310479"}
    start_urls = ["https://www.reiss.com/storelocator/data/stores"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["Stores"]:
            yield Request(
                url="https://www.reiss.com/storelocator/{}/{}".format(
                    location["NA"].lower().replace(" ", ""), location["BR"]
                ),
                meta={"id": location["BR"]},
                callback=self.parse_sd,
            )

    def post_process_item(self, item, response, ld_data, **kwargs):
        if m := re.search(r"\"&daddr=\"\s*\+\s*(-?\d+\.\d+)\s*\+\s*\",\"\s*\+\s*(-?\d+\.\d+);", response.text):
            item["lat"], item["lon"] = m.groups()
        item["ref"] = response.meta["id"]
        item["website"] = response.url
        item.pop("facebook", None)
        item.pop("twitter", None)
        if "John Lewis" in item["name"]:
            item["located_in"] = JohnLewisSpider.item_attributes["brand"]
            item["located_in_wikidata"] = JohnLewisSpider.item_attributes["brand_wikidata"]
        elif "Fenwick" in item["name"]:
            item["located_in"] = "Fenwick"
            item["located_in_wikidata"] = "Q5443673"
        elif "Selfridges" in item["name"]:
            item["located_in"] = "Selfridges"
            item["located_in_wikidata"] = "Q1475656"
        yield item
