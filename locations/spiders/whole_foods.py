from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class WholeFoodsSpider(SitemapSpider, StructuredDataSpider):
    name = "whole_foods"
    item_attributes = {"brand": "Whole Foods Market", "brand_wikidata": "Q1809448"}
    allowed_domains = ["wholefoodsmarket.com"]
    sitemap_urls = ["https://www.wholefoodsmarket.com/robots.txt"]
    sitemap_rules = [(r"/stores/([^/]+)$", "parse")]
    wanted_types = ["Store"]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["image"] = None
        item["branch"] = response.xpath("//h1/text()").get().strip()
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
