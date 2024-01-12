from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysATSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_at"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.at/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.at\/en_at\/(?!search$)[^/]+$", "parse_sd")]
