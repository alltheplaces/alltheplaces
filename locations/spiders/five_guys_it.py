from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysITSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_it"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.cn/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.it\/en_it\/[^/]+$", "parse_sd")]
