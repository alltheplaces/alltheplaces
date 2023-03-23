from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class HSBCARSpider(CrawlSpider, StructuredDataSpider):
    name = "hsbc_ar"
    item_attributes = {"brand": "HSBC", "brand_wikidata": "Q190464", "extras": Categories.BANK.value}
    start_urls = ["https://www.hsbc.com.ar/branch-list/"]
    rules = [Rule(LinkExtractor(allow="/branch-list/"), callback="parse_sd")]
