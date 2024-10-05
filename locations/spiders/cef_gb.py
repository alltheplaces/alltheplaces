from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.structured_data_spider import StructuredDataSpider


class CefGBSpider(CrawlSpider, StructuredDataSpider):
    name = "cef_gb"
    item_attributes = {"brand": "City Electrical Factors", "brand_wikidata": "Q116495226"}
    start_urls = ["https://www.cef.co.uk/stores/directory"]
    rules = [
        Rule(LinkExtractor(restrict_xpaths='//a[@rel="next"]')),
        Rule(LinkExtractor(allow="/stores/", restrict_xpaths='//ul[@id="directory"]'), callback="parse_sd"),
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    requires_proxy = True

