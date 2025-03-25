from scrapy.spiders import SitemapSpider

from locations.spiders.taco_bell_us import TACO_BELL_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class TacoBellGBSpider(SitemapSpider, StructuredDataSpider):
    name = "taco_bell_gb"
    item_attributes = TACO_BELL_SHARED_ATTRIBUTES
    sitemap_urls = ["https://locations.tacobell.co.uk/sitemap.xml"]
    sitemap_rules = [(r"uk/[^/]+/[^/]+\.html$", "parse")]
    drop_attributes = {"image", "name"}
