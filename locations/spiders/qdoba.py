from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class QdobaSpider(SitemapSpider, StructuredDataSpider):
    name = "qdoba"
    item_attributes = {"brand": "Qdoba", "brand_wikidata": "Q1363885"}
    allowed_domains = ["qdoba.com"]
    sitemap_urls = ["https://locations.qdoba.com/sitemap.xml"]
    sitemap_rules = [(r"com/[^/]+/[^/]+/[^/]+/.*", "parse")]
    wanted_types = ["Organization"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if ld_data.get("geo"):
            item["name"] = None
            yield item
