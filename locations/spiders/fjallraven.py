from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class FjallravenSpider(CrawlSpider, StructuredDataSpider):
    name = "fjallraven"
    item_attributes = {
        "brand": "Fjällräven",
        "brand_wikidata": "Q1422481",
        "extras": Categories.SHOP_CLOTHES.value,
    }
    allowed_domains = ["stores.fjallraven.com"]
    start_urls = ["https://stores.fjallraven.com/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/[^/]*/[^/]*/[^/]*/$"),
            follow=True,
            callback="parse_sd",
        ),
    ]
