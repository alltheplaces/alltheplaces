from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class TheRangeSpider(CrawlSpider, StructuredDataSpider):
    name = "the_range"
    item_attributes = {"brand": "The Range", "brand_wikidata": "Q7759409"}
    start_urls = ["https://www.therange.co.uk/stores/"]
    rules = [Rule(LinkExtractor(allow=r"/stores/\w+"), callback="parse_sd")]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
