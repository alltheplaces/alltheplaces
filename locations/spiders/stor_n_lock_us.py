from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class StorNLockUSSpider(SitemapSpider, StructuredDataSpider):
    name = "stor_n_lock_us"
    item_attributes = {"brand": "Stor-N-Lock", "name": "Stor-N-Lock"}
    sitemap_urls = ["https://www.stor-n-lock.com/sitemap.xml"]
    sitemap_rules = [(r"/self-storage/[a-z]{2}/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url
        item.pop("name", None)
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
