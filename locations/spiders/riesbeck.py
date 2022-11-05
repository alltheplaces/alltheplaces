import scrapy

from locations.linked_data_parser import LinkedDataParser


class RiesbeckSpider(scrapy.Spider):
    name = "riesbeck"
    item_attributes = {"brand": "Riesbeck's", "brand_wikidata": "Q28226114"}
    allowed_domains = ["www.riesbeckfoods.com"]
    start_urls = ["https://www.riesbeckfoods.com/stores"]

    def parse(self, response):
        yield from response.follow_all(css="section a", callback=self.parse_store)

    def parse_store(self, response):
        item = LinkedDataParser.parse(response, "Store")
        if item is not None:
            item["ref"] = response.url
        return item
