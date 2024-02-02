from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysSASpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_sa"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.sa/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.sa\/en_sa\/[^/]+$", "parse_sd")]
