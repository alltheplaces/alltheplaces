from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class PjsCoffeeUSSpider(CrawlSpider, StructuredDataSpider):
    name = "pjs_coffee_us"
    item_attributes = {"brand_wikidata": "Q120513813"}
    start_urls = ["https://locations.pjscoffee.com/"]
    rules = [
        Rule(LinkExtractor(r"/\w\w/(?:\w+/)?$")),
        Rule(LinkExtractor(r"/\w\w/\w+/coffee-shop-(\w\w\d{4})\.html$"), callback="parse"),
    ]
    wanted_types = ["CafeOrCoffeeShop"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None

        yield item
