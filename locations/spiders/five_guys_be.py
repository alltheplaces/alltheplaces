from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysBESpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_be"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.be/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.be\/en_be\/[^/]+$", "parse_sd")]
