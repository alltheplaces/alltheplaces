from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class TriumphSpider(SitemapSpider, StructuredDataSpider):
    name = "triumph"
    item_attributes = {"brand": "Triumph", "brand_wikidata": "Q671216"}
    allowed_domains = ["storelocator.triumph.com"]
    sitemap_urls = ["https://storelocator.triumph.com/en/sitemap.xml"]
    sitemap_rules = [(r"/en/.+/triumph-[-\w]+-(\d+)/?$", "parse_sd")]
    drop_attributes = {"facebook"}

    def pre_process_data(self, ld_data: dict, **kwargs):
        ld_data.pop("@id", None)  # capture store id as ref instead of website

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if "Partner" in item["name"].title():
            return
        if "Outlet" in item["name"].title():
            item["name"] = "Triumph Outlet"
        else:
            item["name"] = "Triumph"
        yield item
