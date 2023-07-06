from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AdvanceautopartsSpider(SitemapSpider, StructuredDataSpider):
    name = "advanceautoparts"
    item_attributes = {"brand": "Advance Auto Parts", "brand_wikidata": "Q4686051"}
    allowed_domains = ["stores.advanceautoparts.com"]
    sitemap_urls = ["https://stores.advanceautoparts.com/robots.txt"]
    sitemap_rules = [(r"^https://stores.advanceautoparts.com/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["AutoPartsStore"]

    def sitemap_filter(self, entries):
        for entry in entries:
            if entry["loc"].startswith("https://stores.advanceautoparts.com/es"):
                continue
            yield entry
