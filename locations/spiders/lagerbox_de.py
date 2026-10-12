from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LagerboxDESpider(SitemapSpider, StructuredDataSpider):
    name = "lagerbox_de"
    item_attributes = {"brand": "Lagerbox", "name": "Lagerbox"}
    sitemap_urls = ["https://www.lagerbox.com/sitemap.xml"]
    sitemap_rules = [(r"/lagerraum-mieten-[^/]+/[^/]+$", "parse_sd")]
    drop_attributes = {"facebook", "twitter", "image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name", None)
        if item.get("phone") and item["phone"].replace(" ", "").endswith("0800222666999"):
            item["phone"] = None
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
