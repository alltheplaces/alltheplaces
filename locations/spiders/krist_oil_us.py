from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser


class KristOilUSSpider(Spider):
    name = "krist_oil_us"
    item_attributes = {"brand": "Krist Oil", "brand_wikidata": "Q77885501"}
    allowed_domains = ["kristoil.com"]
    start_urls = ["https://kristoil.com/wp-content/themes/krist-2020-jan13v2/ajax/map.php"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json().values():
            item = DictParser.parse(location["location"])
            item["ref"] = location["ID"]
            item["name"] = location["title"]
            item["addr_full"] = location.pop("street_address", location.get("address"))
            item["phone"] = location["phone"]
            yield item
