from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class BlackberrysINSpider(CrawlSpider, StructuredDataSpider):
    name = "blackberrys_in"
    item_attributes = {"brand": "Blackberrys", "brand_wikidata": "Q4922570"}
    start_urls = ["https://stores.blackberrys.com/"]
    rules = [Rule(LinkExtractor(r"page=\d+$")), Rule(LinkExtractor("/Home"), callback="parse_sd")]
    wanted_types = ["Store"]
