from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class AdvanceAutoPartsUSSpider(SitemapSpider, StructuredDataSpider):
    name = "advance_auto_parts_us"
    item_attributes = {"brand": "Advance Auto Parts", "brand_wikidata": "Q4686051"}
    allowed_domains = ["stores.advanceautoparts.com"]
    sitemap_urls = ["https://stores.advanceautoparts.com/robots.txt"]
    sitemap_rules = [(r"^https:\/\/stores\.advanceautoparts\.com\/(?!es\/)[^/]+/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item.pop("twitter", None)
        item.pop("image", None)
        yield item
