import scrapy

from locations.dict_parser import DictParser


class FreshMarketSpider(scrapy.Spider):
    name = "fresh_market"
    item_attributes = {
        "brand": "Fresh Market",
        "brand_wikidata": "Q7735265",
        "country": "US",
    }
    start_urls = ["https://api.thefreshmarket.com/v1/stores?page[number]=1&page[size]=200&Filter[radius]=100000"]

    def parse(self, response):
        for store in response.json()["data"]:
            store.update(store.pop("attributes"))
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")
            yield item
