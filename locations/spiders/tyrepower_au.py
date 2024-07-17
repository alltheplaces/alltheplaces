from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class TyrepowerAUSpider(Spider):
    name = "tyrepower_au"
    item_attributes = {"brand": "Tyrepower", "brand_wikidata": "Q108855867"}
    allowed_domains = ["tyrepower.com.au"]
    start_urls = ["https://www.tyrepower.com.au/stores/google-store-search"]
    no_refs = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["all_stores"]:
            item = DictParser.parse(location)
            item["street_address"] = clean_address([location["address1"], location["address2"]])
            if location.get("websiteUrl"):
                item["website"] = location["websiteUrl"]
            elif location.get("url"):
                item["website"] = "https://www.tyrepower.com.au/" + location["url"]
            yield item
