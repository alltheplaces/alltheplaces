from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class PureBarreUSSpider(Spider):
    name = "pure_barre_us"
    item_attributes = {"brand": "Pure Barre", "brand_wikidata": "Q86707084"}
    allowed_domains = ["members.purebarre.com"]
    start_urls = ["https://members.purebarre.com/api/brands/purebarre/locations?open_status=external"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["locations"]:
            if location.get("coming_soon") or location.get("open_status") != "open":
                continue
            item = DictParser.parse(location)
            item["ref"] = location.get("seq")
            item.pop("addr_full", None)
            item["street_address"] = ", ".join(filter(None, [location.get("address"), location.get("address2")]))
            item["website"] = location.get("site_url")
            yield item
