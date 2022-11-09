from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class HSBCUKGBSpider(CrawlSpider, StructuredDataSpider):
    name = "hsbc_uk"
    item_attributes = {"brand": "HSBC UK", "brand_wikidata": "Q64767453"}
    start_urls = ["https://www.hsbc.co.uk/branch-list/"]
    rules = [Rule(LinkExtractor(allow=r"/branch-list/"), callback="parse_sd")]
