import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class AtticStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "attic_storage_us"
    item_attributes = {"brand": "Attic Storage"}
    sitemap_urls = ["https://www.attic-storage.com/sitemap.xml"]
    sitemap_rules = [("", "parse_sd")]
    drop_attributes = {"email", "image"}

    def post_process_item(self, item: Feature, response, ld_data, **kwargs):
        item["branch"] = re.sub(r"^Attic Storage( of| at| on)? ", "", item.pop("name", ""))
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
