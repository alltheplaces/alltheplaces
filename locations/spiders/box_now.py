from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class BoxNowSpider(Spider):
    name = "box_now"
    item_attributes = {"brand": "Box Now"}
    start_urls = [
        "https://boxlockersloadfilesbg.blob.core.windows.net/lockerslargenavigate/all.json",
        "https://boxlockersloadfiles.blob.core.windows.net/lockerslargenavigate/all.json",
        "https://boxlockersloadfilescr.blob.core.windows.net/lockerslargenavigate/all.json",
    ]
    # requires_proxy = "BG"

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location_id, location in response.json().items():
            item = DictParser.parse(location)
            if "boxlockersloadfilesbg.blob.core.windows.net" in response.url:
                item["country"] = "BG"
                item["brand_wikidata"] = "Q117195372"
            elif "boxlockersloadfiles.blob.core.windows.net" in response.url:
                item["country"] = "GR"
                item["brand_wikidata"] = "Q117195376"
            elif "boxlockersloadfilescr.blob.core.windows.net" in response.url:
                item["country"] = "HR"
                item["brand_wikidata"] = "Q117195375"
            yield item
