from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class StoreSpaceUSSpider(SitemapSpider, StructuredDataSpider):
    name = "store_space_us"
    item_attributes = {"brand": "Store Space", "brand_wikidata": "Q121464701"}
    sitemap_urls = ["https://www.storespace.com/facilities-sitemap.xml"]
    sitemap_rules = [(r"/storage-locations/[^/]+/storage-units-in-", "parse_sd")]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
