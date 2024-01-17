from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysNLSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_nl"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.nl/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.nl\/en_nl\/[^/]+$", "parse_sd")]
