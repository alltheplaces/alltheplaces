from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysHKSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_hk"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.com.hk/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/restaurants\.fiveguys\.com\.hk\/en_hk\/(?!search$)[^/]+$", "parse_sd")]
