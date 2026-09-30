from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class OhmyboxESSpider(SitemapSpider, StructuredDataSpider):
    name = "ohmybox_es"
    item_attributes = {"brand": "OhMyBox!"}
    sitemap_urls = ["https://www.ohmybox.es/sitemap.xml"]
    sitemap_rules = [(r"/trasteros/[^/]+/[^/]+/$", "parse_sd")]
    drop_attributes = {"image", "twitter"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        if not item["name"].startswith("OhMyBox! - "):
            return
        item["branch"] = item.pop("name").removeprefix("OhMyBox! - ")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
