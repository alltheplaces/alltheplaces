from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysKWSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_kw"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.com.kw/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.com\.kw\/en_kw\/[^/]+$", "parse_sd")]
