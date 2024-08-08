from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysMOSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_mo"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.mo/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/restaurants\.fiveguys\.mo\/en_mo\/(?!search$)[^/]+$", "parse_sd")]
