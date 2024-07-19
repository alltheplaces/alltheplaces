from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CellOnlySpider(SitemapSpider, StructuredDataSpider):
    name = "cell_only"
    item_attributes = {"brand": "CellOnly"}
    allowed_domains = ["cell-only.com"]
    sitemap_urls = ["https://locations.cell-only.com/sitemap.xml"]
    sitemap_rules = [
        (r"https://locations.cell-only.com/[-\w]+/[-\w]+/[-\w]+", "parse_sd"),
    ]
    wanted_types = ["MobilePhoneStore"]
