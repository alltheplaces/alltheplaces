import scrapy

from locations.dict_parser import DictParser


class HermesSpider(scrapy.Spider):
    name = "hermes"
    item_attributes = {
        "brand": "Hermes",
        "brand_wikidata": "Q843887",
    }
    allowed_domains = ["hermes.com"]
    start_urls = ["https://bck.hermes.com/stores?lang=en"]

    def parse(self, response):
        for store in response.json().get("shops"):
            store["location"] = store.pop("geoCoordinates")
            item = DictParser.parse(store)
            item["ref"] = store.get("shopId")
            item["website"] = f'https://www.hermes.com/uk/en/{store["url"]}'

            yield item
