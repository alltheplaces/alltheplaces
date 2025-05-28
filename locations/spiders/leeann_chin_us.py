from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class LeeannChinUSSpider(CrawlSpider, StructuredDataSpider):
    name = "leeann_chin_us"
    item_attributes = {
        "brand": "Leeann Chin",
        "brand_wikidata": "Q6515716",
    }
    start_urls = ["https://www.leeannchin.com/locations"]
    rules = [Rule(LinkExtractor(allow=r"/restaurant/[-\w]+/[-\w]+/?$"), callback="parse_sd")]
