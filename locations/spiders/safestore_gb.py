from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class SafestoreGBSpider(SitemapSpider, StructuredDataSpider):
    name = "safestore_gb"
    item_attributes = {"brand": "Safestore", "brand_wikidata": "Q20713915"}
    allowed_domains = ["safestore.co.uk"]
    sitemap_urls = ["https://www.safestore.co.uk/robots.txt"]
    sitemap_rules = [(r"/(self-)?storage/", "parse_sd")]
    wanted_types = ["Selfstorage"]
    convert_microdata = False
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").strip().removeprefix("Safestore - ")
        if not item.get("lat"):
            item["lat"] = ld_data.get("latitude")
        if not item.get("lon"):
            item["lon"] = ld_data.get("longitude")
        apply_category(Categories.SHOP_STORAGE_RENTAL, item)
        yield item
