from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class KfcATSpider(SitemapSpider, StructuredDataSpider):
    name = "kfc_at"
    item_attributes = KFC_SHARED_ATTRIBUTES
    sitemap_urls = ["https://kfc.co.at/sitemap.xml"]
    sitemap_rules = [(r"/restaurants/", "parse")]
    wanted_types = ["Restaurant"]
    search_for_image = False

    def post_process_item(self, item: Feature, response, ld_data, **kwargs):
        item["email"] = None
        item["branch"] = item.pop("name").removeprefix("KFC ")
        apply_category(Categories.FAST_FOOD, item)
        yield item
