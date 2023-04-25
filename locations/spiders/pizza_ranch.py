import json

import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class PizzaRanchSpider(CrawlSpider, StructuredDataSpider):
    name = "pizza_ranch_us"
    item_attributes = {"brand": "Pizza Ranch", "brand_wikidata": "Q7199978"}
    allowed_domains = ["pizzaranch.com"]
    start_urls = ("https://pizzaranch.com/all-locations",)
    rules = [
        Rule(LinkExtractor(allow=r"/all-locations/search-results/"), callback="parse_search_results"),
    ]

    def parse_search_results(self, response):
        json_str = response.xpath("//script/text()")[-2].extract()[21:-4]
        json_data = json.loads(json_str)

        for s in json_data:
            yield scrapy.Request(url=s["website"], callback=self.parse_sd)
