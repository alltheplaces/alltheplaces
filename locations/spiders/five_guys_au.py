from scrapy.spiders import SitemapSpider

from locations.spiders.five_guys_us import FiveGuysUSSpider
from locations.structured_data_spider import StructuredDataSpider


class FiveGuysAUSpider(SitemapSpider, StructuredDataSpider):
    name = "five_guys_au"
    item_attributes = FiveGuysUSSpider.item_attributes
    sitemap_urls = ["https://restaurants.fiveguys.com.au/sitemap.xml"]
    sitemap_rules = [(r"^https://restaurants\.fiveguys\.com\.au\/(?!(index\.html$|search$))[^/]+$", "parse_sd")]
