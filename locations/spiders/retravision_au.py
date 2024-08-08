from scrapy.spiders import SitemapSpider

from locations.categories import Categories
from locations.structured_data_spider import StructuredDataSpider


class RetravisionAUSpider(SitemapSpider, StructuredDataSpider):
    name = "retravision_au"
    item_attributes = {
        "brand": "Retravision",
        "brand_wikidata": "Q7316908",
        "extras": Categories.SHOP_ELECTRONICS.value,
    }
    allowed_domains = ["www.retravision.com.au"]
    sitemap_urls = ["https://www.retravision.com.au/sitemap-stores.xml"]
    sitemap_rules = [
        (
            r"^https:\/\/www\.retravision\.com\.au\/stores\/[\w\-]+$",
            "parse_sd",
        ),
    ]
    requires_proxy = "AU"

    def post_process_item(self, item, response, ld_data):
        item.pop("facebook")
        item.pop("image", "")
        yield item
