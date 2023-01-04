import scrapy

from locations.dict_parser import DictParser
from locations.geo import point_locations


class BirkenstockUsSpider(scrapy.Spider):
    name = "birkenstock_us"
    item_attributes = {
        "brand": "Birkenstock",
        "brand_wikidata": "Q648458",
    }
    allowed_domains = ["birkenstock.com"]
    start_urls = [
        "https://www.birkenstock.com/on/demandware.store/Sites-US-Site/en_US/Stores-GetStoresJson?latitude=40.724351&longitude=-74.001120&storeid=&distance=10000&distanceunit=mi&searchText=&countryCode=US&storeLocatorType=regular&storetype1=true"
    ]

    def parse(self, response):
        for _, data in response.json().get("stores").items():
            item = DictParser.parse(data)
            item["website"] = data.get("storeDetailsFlyinLink")
            yield item
