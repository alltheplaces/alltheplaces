from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysCHSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_ch"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.ch/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.ch\/en_ch\/[^/]+$", "parse_sd")]
