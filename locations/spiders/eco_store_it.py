from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EcoStoreITSpider(SitemapSpider, StructuredDataSpider):
    name = "eco_store_it"
    item_attributes = {
        "brand": "Eco Store",
        "brand_wikidata": "Q126483871",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False}
    sitemap_urls = ["https://www.ecostore.it/store-sitemap.xml"]
    sitemap_rules = [("/store/", "parse_sd")]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        apply_category(Categories.SHOP_PRINTER_INK, item)
        yield item
