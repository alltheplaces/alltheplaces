from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class StopAndShopUSSpider(SitemapSpider, StructuredDataSpider):
    name = "stop_and_shop_us"
    item_attributes = {"brand": "Stop & Shop", "brand_wikidata": "Q3658429"}
    sitemap_urls = ["https://stores.stopandshop.com/sitemap.xml"]
    sitemap_rules = [(r"^https://stores\.stopandshop\.com/\w\w/[^/]+/[^/]+$", "parse")]
    wanted_types = ["GroceryStore"]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Stop & Shop ")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
