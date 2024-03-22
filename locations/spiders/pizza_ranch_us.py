import json

from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.dict_parser import DictParser
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
        for store in json_data:
            if website := store["website"]:
                yield Request(url=website, callback=self.parse_sd)
            else:
                item = DictParser.parse(store)
                item["website"] = "https://pizzaranch.com/"
                yield item
