from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class NicholsonsPubsGBSpider(CrawlSpider, StructuredDataSpider, PlaywrightSpider):
    name = "nicholsons_pubs_gb"
    item_attributes = {"brand": "Nicholson's", "brand_wikidata": "Q113130666"}
    start_urls = ["https://www.nicholsonspubs.co.uk/ourvenues"]
    rules = [Rule(LinkExtractor("/restaurants/"), "parse_sd")]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS
