from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class ScrewfixGBSpider(CrawlSpider, StructuredDataSpider):
    name = "screwfix_gb"
    item_attributes = {"brand": "Screwfix", "brand_wikidata": "Q7439115"}
    allowed_domains = ["www.screwfix.com"]
    download_delay = 0.1
    start_urls = ["https://www.screwfix.com/stores/all"]
    rules = [Rule(LinkExtractor(allow=r"\/stores\/([A-Z][A-Z][0-9])\/.+$"), callback="parse_sd")]
    wanted_types = ["HardwareStore"]
