from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class DevonSelfStorageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "devon_self_storage_us"
    item_attributes = {"brand": "Devon Self Storage", "brand_wikidata": "Q127502283"}
    allowed_domains = ["www.devonselfstorage.com"]
    sitemap_urls = ["https://www.devonselfstorage.com/sitemap.xml"]
    sitemap_rules = [(r"/storage-locations/[a-z]{2}/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]
    time_format = "%I:%M %p"
    drop_attributes = {"image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = item["website"]
        item["name"] = None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
