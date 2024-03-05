from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysAESpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_ae"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.ae/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.ae\/en_ae\/[^/]+$", "parse_sd")]
