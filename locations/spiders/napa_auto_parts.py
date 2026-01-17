from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class NapaAutoPartsSpider(SitemapSpider, StructuredDataSpider):
    name = "napa_auto_parts"
    custom_settings = {
        "DOWNLOAD_DELAY": 5,
        "USER_AGENT": None,
    }
    requires_proxy = True
    item_attributes = {"brand": "NAPA Auto Parts", "brand_wikidata": "Q6970842"}
    sitemap_urls = ["https://www.napaonline.com/nol_store_sitemap_https.xml"]
    sitemap_rules = [
        (r"^https://www.napaonline.com/en/\w+/[^/]+/store/(\d+)$", "parse"),
    ]
    search_for_facebook = False
    search_for_twitter = False
    drop_attributes = ["image"]
    time_format = "%H:%M:%S"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name").removeprefix("NAPA Auto Parts - ")
        apply_category(Categories.SHOP_CAR_PARTS, item)
        yield item
