from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.spiders.hsbc import HSBCSpider
from locations.structured_data_spider import StructuredDataSpider


class HSBCUSSpider(CrawlSpider, StructuredDataSpider):
    name = "hsbc_us"
    item_attributes = HSBCSpider.item_attributes
    start_urls = ["https://www.us.hsbc.com/wealth-center/list/"]
    rules = [Rule(LinkExtractor(allow=r"/wealth-center/list/"), callback="parse_sd")]
