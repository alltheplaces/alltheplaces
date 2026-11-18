from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class CycleSpotJPSpider(CrawlSpider, StructuredDataSpider):
    name = "cycle_spot_jp"
    item_attributes = {
        "brand": "サイクルスポット",
        "brand_wikidata": "Q93620124",
        "extras": Categories.SHOP_BICYCLE.value,
    }
    allowed_domains = ["www.cyclespot.net"]
    start_urls = ["https://www.cyclespot.net/shops-list"]
    rules = [
        Rule(
            LinkExtractor(
                allow=r"/pages/store/[^/]+",
            ),
            callback="parse_sd",
        ),
    ]
    wanted_types = ["BikeStore"]
