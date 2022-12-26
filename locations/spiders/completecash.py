from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CompleteCashSpider(SitemapSpider, StructuredDataSpider):
    name = "completecash"
    item_attributes = {"brand": "Complete Cash"}
    allowed_domains = ["locations.completecash.net"]
    sitemap_urls = ["https://locations.completecash.net/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    wanted_types = ["Place"]
