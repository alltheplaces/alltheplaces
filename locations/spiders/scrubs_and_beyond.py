from scrapy.spiders import SitemapSpider
from locations.structured_data_spider import StructuredDataSpider


class ScrubsAndBeyondSpider(SitemapSpider, StructuredDataSpider):

    name = "scrubs_and_beyond"
    item_attributes = {"brand": "Scrubs and Beyond"}
    allowed_domains = ["locations.scrubsandbeyond.com"]
    sitemap_urls = ("https://locations.scrubsandbeyond.com/robots.txt",)
    sitemap_rules = [
        (r"^https://locations.scrubsandbeyond.com/[^/]+/[^/]+/[^/]+.html$", "parse_sd"),
    ]
    wanted_types = ["Hospital"]
