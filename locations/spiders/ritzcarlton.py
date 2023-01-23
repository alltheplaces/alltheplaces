import json

import scrapy

from locations.linked_data_parser import LinkedDataParser


class RitzCarltonSpider(scrapy.Spider):
    name = "ritzcarlton"
    item_attributes = {
        "brand": "The Ritz Carlton",
        "brand_wikidata": "Q782200",
    }
    start_urls = ["https://www.ritzcarlton.com/en/hotels"]
    custom_settings = {"REDIRECT_ENABLED": "False"}

    def parse(self, response):
        urls = response.xpath('//div[@class="accordion"]//a[not(@id="upcoming ")]')
        for url in urls:
            yield scrapy.Request(url=url.xpath("./@href").get(), callback=self.parse_hotels)

    def parse_hotels(self, response):
        if item := LinkedDataParser.parse(response, "Hotel"):
            if coords := response.xpath("//@data-map-settings").get():
                coords = json.loads(coords)
                item["lat"] = coords.get("mapCenter", {}).get("latitude")
                item["lon"] = coords.get("mapCenter", {}).get("longitude")
            item["ref"] = response.url

            yield item
