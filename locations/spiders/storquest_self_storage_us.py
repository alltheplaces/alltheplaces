from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class StorquestSelfStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "storquest_self_storage_us"
    item_attributes = {
        "brand": "StorQuest Self Storage",
        "brand_wikidata": "Q109337134",
        "name": "StorQuest Self Storage",
    }
    sitemap_urls = ["https://www.storquest.com/sitemap.xml"]
    sitemap_rules = [(r"/self-storage/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
