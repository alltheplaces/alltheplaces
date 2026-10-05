from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SelfstockFRSpider(SitemapSpider, StructuredDataSpider):
    name = "selfstock_fr"
    item_attributes = {"brand": "Selfstock", "name": "Selfstock"}
    sitemap_urls = ["https://selfstock.com/sitemaps/centers/sitemap.xml"]
    sitemap_rules = [(r"/centres-de-selfstockage/", "parse_sd")]
    drop_attributes = {"image", "opening_hours"}

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name", None)
        if item.get("postcode") and item.get("street_address"):
            item["street_address"] = item["street_address"].split(f", {item['postcode']}")[0]
        item["ref"] = response.url
        item["website"] = response.url
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
