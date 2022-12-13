import scrapy

from locations.dict_parser import DictParser


class AsicsDeSpider(scrapy.Spider):

    name = "asics_de"
    item_attributes = {"brand": "asics", "brand_wikidata": "Q327247"}
    allowed_domains = ["www.asics.com"]
    start_urls = ["https://cdn.crobox.io/content/ujf067/stores.json"]

    def parse(self, response):
        for store in response.json():
            item = DictParser.parse(store)
            item["ref"] = store["name"]
            yield item
