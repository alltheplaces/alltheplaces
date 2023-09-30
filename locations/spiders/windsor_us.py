from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class WindsorUSSpider(Spider):
    name = "windsor_us"
    item_attributes = {"brand": "Windsor", "brand_wikidata": "Q72981668"}
    allowed_domains = ["www.windsorstore.com"]
    start_urls = ["https://www.windsorstore.com/cdn/shop/t/8/assets/stores.json"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            if (
                "CLOSED" in location["properties"]["name"].upper().split()
                or "COMING" in location["properties"]["name"].upper().split()
            ):
                continue
            item = DictParser.parse(location["properties"])
            item["ref"] = location["properties"]["store_number"]
            item["lat"] = location["geometry"]["coordinates"][0]
            item["lon"] = location["geometry"]["coordinates"][1]
            item["street_address"] = location["properties"]["street_1"]
            if location["properties"].get("url"):
                item["website"] = "https://www.windsorstore.com" + location["properties"]["url"]
            yield item
