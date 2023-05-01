import scrapy

from locations.linked_data_parser import LinkedDataParser


class FuddruckersSpider(scrapy.Spider):
    name = "fuddruckers"
    item_attributes = {"brand": "Fuddruckers", "brand_wikidata": "Q5507056"}
    start_urls = ["http://www.fuddruckers.com/services/location/get_stores_by_position.php"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response):
        results = response.json()
        for store in results["places"]["positions"]["data"]:
            url = "https://www.fuddruckers.com" + store["link"]
            yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "Restaurant")
        item["ref"] = item["website"]
        yield item
