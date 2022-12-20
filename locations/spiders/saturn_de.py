from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class SaturnSpider(CrawlSpider, StructuredDataSpider):
    name = "saturn_de"
    item_attributes = {"brand": "Saturn", "brand_wikidata": "Q2543504"}
    allowed_domains = ["www.saturn.de"]
    start_urls = ["https://www.saturn.de/de/store/store-finder"]
    rules = [Rule(LinkExtractor(allow="de/store"), callback="parse_sd", follow=False)]
    wanted_types = ["Store"]
