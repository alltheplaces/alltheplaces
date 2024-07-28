from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysMYSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_my"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.my/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/restaurants\.fiveguys\.my\/en\/[^/]+$", "parse_sd")]
