from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class MyplaceSelfstorageDESpider(SitemapSpider, StructuredDataSpider):
    name = "myplace_selfstorage_de"
    item_attributes = {"brand": "MyPlace-SelfStorage", "brand_wikidata": "Q109659129"}
    sitemap_urls = ["https://www.myplace.de/sitemap-0.xml"]
    sitemap_rules = [(r"/de/standorte/[^/]+/[^/]+$", "parse_sd")]
    drop_attributes = {"facebook", "twitter", "image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        if item.get("phone") and item["phone"].replace(" ", "").endswith("800591591010"):
            item["phone"] = None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
