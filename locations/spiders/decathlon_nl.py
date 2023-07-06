from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.spiders.decathlon import Decathlon
from locations.structured_data_spider import StructuredDataSpider


class DecathlonNLSpider(CrawlSpider, StructuredDataSpider):
    name = "decathlon_nl"
    item_attributes = Decathlon.item_attributes
    start_urls = ["https://www.decathlon.nl/store-locator"]
    rules = [
        Rule(
            LinkExtractor(allow="/store-view/"),
            callback="parse_sd",
        )
    ]
    wanted_types = ["SportingGoodsStore"]
