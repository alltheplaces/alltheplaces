import json

from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

from locations.linked_data_parser import LinkedDataParser


class CrateAndBarrelSpider(CrawlSpider):
    name = "crateandbarrel"
    allowed_domains = ["www.crateandbarrel.com"]
    item_attributes = {"brand": "crateandbarrel", "brand_wikidata": "Q5182604"}
    start_urls = ["https://www.crateandbarrel.com/stores/list-state/retail-stores"]
    rules = [
        Rule(
            LinkExtractor(allow=r"stores\/list-state\/retail-stores\/([a-zA-Z]{2})$"),
            callback="parse",
        )
    ]

    def parse(self, response):
        for ldjson in response.xpath(
            "//script[@type='application/ld+json' and contains(text(), '\"@type\":\"Store\"')]/text()"
        ).extract():
            data = json.loads(ldjson)
            item = LinkedDataParser.parse_ld(data)
            print("Item: ", item)
            item["ref"] = item["website"] = response.url
            yield item
