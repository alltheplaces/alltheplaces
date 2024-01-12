from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysLUSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_lu"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.lu/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.lu\/en_lu\/[^/]+$", "parse_sd")]
