
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class MossGBSpider(CrawlSpider, StructuredDataSpider):
    name = "moss_gb"
    item_attributes = {
        "brand": "Moss Bros",
        "brand_wikidata": "Q6916538",
        "country": "GB",
    }

    start_urls = ["https://www.moss.co.uk/store/finder"]
    rules = [Rule(LinkExtractor(allow=r"/store/([^/]+)$"), callback="parse_sd")]
    wanted_types = ["Store"]
