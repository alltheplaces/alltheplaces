from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class AceHardwareSpider(CrawlSpider, StructuredDataSpider):
    name = "ace_hardware"
    item_attributes = {"brand": "Ace Hardware", "brand_wikidata": "Q4672981"}
    start_urls = ["https://www.acehardware.com/store-directory"]
    rules = [Rule(LinkExtractor(allow="/store-details/"), callback="parse_sd")]
    user_agent = BROWSER_DEFAULT
