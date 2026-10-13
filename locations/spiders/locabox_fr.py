from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class LocaboxFRSpider(SitemapSpider, StructuredDataSpider):
    name = "locabox_fr"
    item_attributes = {"brand": "Locabox", "name": "Locabox"}
    sitemap_urls = ["https://www.locabox.fr/sitemap.xml"]
    sitemap_rules = [(r"^https://www\.locabox\.fr/garde-meuble-[^/]+$", "parse_sd")]
    drop_attributes = {"facebook", "image"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item.pop("name", None)
        item["ref"] = response.url
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
