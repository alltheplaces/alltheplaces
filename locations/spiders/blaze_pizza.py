import scrapy

from locations.dict_parser import DictParser


class BlazePizzaSpider(scrapy.Spider):
    name = "blaze_pizza"
    item_attributes = {"brand": "Blaze Pizza", "brand_wikidata": "Q23016666"}
    allowed_domains = ["nomnom-prod-api.blazepizza.com"]
    start_urls = ["https://nomnom-prod-api.blazepizza.com/extras/restaurant/summary/state"]

    def parse(self, response):
        url = "https://nomnom-prod-api.blazepizza.com"
        for data in response.json().get("data"):
            for row in data.get("cities"):
                yield scrapy.Request(url=f'{url}{row.get("datauri")}', callback=self.parse_store)

    def parse_store(self, response):
        item = DictParser.parse(response.json().get("data")[0].get("restaurants")[0])

        yield item
