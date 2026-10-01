from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class AppleSelfStorageCASpider(SitemapSpider, StructuredDataSpider):
    name = "apple_self_storage_ca"
    item_attributes = {"brand": "Apple Self Storage"}
    sitemap_urls = ["https://www.applestorage.com/sitemap.xml"]
    sitemap_rules = [(r"/self-storage/[a-z]{2}/[^/]+/[^/]+/?$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    drop_attributes = {"image", "facebook", "twitter"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("name") != "Apple Self Storage":
            return
        item["ref"] = item["website"]
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
