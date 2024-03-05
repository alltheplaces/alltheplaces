from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysBHSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_bh"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.bh/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.bh\/en_bh\/(?!search$)[^/]+$", "parse_sd")]
