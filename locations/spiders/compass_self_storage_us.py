from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class CompassSelfStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "compass_self_storage_us"
    item_attributes = {
        "brand": "Compass Self Storage",
        "brand_wikidata": "Q120719704",
        "name": "Compass Self Storage",
    }
    sitemap_urls = ["https://www.compassselfstorage.com/sitemap_index.xml"]
    sitemap_follow = ["page-sitemap"]
    sitemap_rules = [(r"/self-storage/[^/]+/[^/]+/", "parse_sd")]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
