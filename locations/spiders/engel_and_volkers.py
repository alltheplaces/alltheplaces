import scrapy

from locations.dict_parser import DictParser


class EngelAndVolkersSpider(scrapy.Spider):
    name = "engel_and_volkers"
    item_attributes = {"brand": "Engel & Völkers", "brand_wikidata": "Q1341765"}
    allowed_domains = ["engelvoelkers.com"]
    start_urls = ["https://www.engelvoelkers.com/api/?source=locations"]

    def parse(self, response):
        for agence in response.json().get("response"):
            template_url = "https://www.engelvoelkers.com/api/?source=locations&id={}"
            yield scrapy.Request(
                template_url.format(agence["id"]),
                callback=self.agence_parse,
            )

    def agence_parse(self, response):
        agence = response.json().get("response")
        item = DictParser.parse(agence)
        item["name"] = agence.get("name", {}).get("en")
        item["website"] = agence.get("contact", {}).get("www")

        yield item
