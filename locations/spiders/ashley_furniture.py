import scrapy

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AshleyFurnitureSpider(scrapy.spiders.SitemapSpider, StructuredDataSpider):
    name = "ashley_furniture"
    item_attributes = {"brand": "Ashley HomeStore", "brand_wikidata": "Q4805437"}
    sitemap_urls = ["https://stores.ashleyfurniture.com/sitemap_index.xml"]
    sitemap_rules = [(r"/store/(?!.*/(?:luxe|mattress|patio-furniture)/$)", "parse_sd")]
    drop_attributes = {"image"}
    wanted_types = ["FurnitureStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
