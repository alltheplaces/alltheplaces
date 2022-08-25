import scrapy
from locations.dict_parser import DictParser


class McDonaldsITSpider(scrapy.Spider):
    name = "mcdonalds_it"
    item_attributes = {"brand": "McDonald's", "brand_wikidata": "Q38076"}
    start_urls = ["https://www.mcdonalds.it/static/json/store_locator.json"]

    def parse(self, response):
        for store in response.json()["sites"]:
            item = DictParser.parse(store)
            item["website"] = "https://www.mcdonalds.it/ristorante/" + store["uri"]
            item["street_address"] = item["addr_full"]
            item["addr_full"] = None
            item["country"] = "IT"
            # TODO: could bounce over to website page for more data
            yield item
