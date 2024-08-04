import scrapy

from locations.dict_parser import DictParser


class AsicsEUSpider(scrapy.Spider):
    name = "asics_eu"
    item_attributes = {"brand": "asics", "brand_wikidata": "Q327247"}
    allowed_domains = ["www.asics.com"]
    start_urls = ["https://cdn.crobox.io/content/ujf067/stores.json"]

    def parse(self, response):
        for store in response.json():
            if store["storetype"] in ["factory-outlet", "retail-store"]:
                item = DictParser.parse(store)
                item["street_address"] = item.pop("addr_full")
                item["ref"] = store["name"]
                item["brand"] = f'ascis {store["storetype"]}'.replace("-", " ").title()
                yield item
