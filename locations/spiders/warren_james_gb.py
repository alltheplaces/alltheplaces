from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class WarrenJamesGBSpider(CrawlSpider, StructuredDataSpider):
    name = "warren_james_gb"
    item_attributes = {"brand": "Warren James", "brand_wikidata": "Q19604616"}
    start_urls = ["https://www.warrenjames.co.uk/shop-locator/"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/shop-locator/[^/]+$"),
            callback="parse_sd",
        )
    ]
    wanted_types = ["localBusiness"]
    drop_attributes = {"facebook"}

