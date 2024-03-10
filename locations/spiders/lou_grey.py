from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class LouGreySpider(SitemapSpider, StructuredDataSpider):
    name = "lou_grey"
    item_attributes = {"brand": "Loft"}
    allowed_domains = ["stores.loft.com"]
    sitemap_urls = ("https://stores.loft.com/sitemap.xml",)
    sitemap_rules = [(r"/\w\w/[-\w]+/[-\w]+\.html$", "parse_sd")]
    wanted_types = ["LocalBusiness"]
