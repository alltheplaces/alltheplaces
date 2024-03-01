from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysIESpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_ie"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.ie/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.ie\/[^/]+$", "parse_sd")]
