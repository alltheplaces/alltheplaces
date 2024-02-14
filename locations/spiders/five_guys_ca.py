from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysCASpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_ca"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.ca/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.ca\/[^/]+$", "parse_sd")]
