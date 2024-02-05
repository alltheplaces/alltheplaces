from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysQASpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_qa"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.qa/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.qa\/en_qa\/[^/]+$", "parse_sd")]
