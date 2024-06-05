import re

from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SecurCareSelfStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "securcare_self_storage_us"
    item_attributes = {"brand": "SecurCare Self Storage", "brand_wikidata": "Q124821649"}
    sitemap_urls = ["https://www.securcareselfstorage.com/robots.txt"]
    sitemap_rules = [("/storage/[^/]+/[^/]+/[^/]+$", "parse")]
    wanted_types = ["SelfStorage"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = None
        if m := re.search(r"lat\\u0022:(-?\d+\.\d+),\\u0022long\\u0022:(-?\d+\.\d+),", response.text):
            item["lat"], item["lon"] = m.groups()
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
