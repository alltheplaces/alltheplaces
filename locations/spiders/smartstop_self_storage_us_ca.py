from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SmartstopSelfStorageUSCASpider(SitemapSpider, StructuredDataSpider):
    name = "smartstop_self_storage_us_ca"
    item_attributes = {
        "brand": "SmartStop Self Storage",
        "brand_wikidata": "Q108738738",
        "name": "SmartStop Self Storage",
    }
    sitemap_urls = ["https://smartstopselfstorage.com/sitemap-locations.xml"]
    sitemap_rules = [(r"/find-storage/[^/]+/[^/]+/[^/]+$", "parse_sd")]
    wanted_types = ["SelfStorage"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        if "SmartStop" not in item["name"]:
            return  # managed facilities operating under other brands
        item["name"] = None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
