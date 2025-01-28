import json

import scrapy
from scrapy.selector import Selector

from locations.linked_data_parser import LinkedDataParser


class JulesSpider(scrapy.Spider):
    name = "jules"
    item_attributes = {"brand": "Jules", "brand_wikidata": "Q3188386"}
    start_urls = ["https://www.jules.com/fr-be/recherche-magasins/", "https://www.jules.com/fr-fr/recherche-magasins/"]

    def parse(self, response):
        stores = json.loads(response.xpath("//@data-locations").get())
        for store in stores:
            website = (
                "https://www.jules.com"
                + Selector(text=store.get("infoWindowHtml")).xpath("//a[@class='link']/@href").get()
            )
            yield scrapy.Request(url=website, callback=self.parse_store)

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "MensClothingStore")
        item["website"] = "https://www.jules.com" + item["website"]
        item["image"] = "https://www.jules.com" + item["image"]
        item["ref"] = response.xpath("//@data-store-id").get()

        yield item
