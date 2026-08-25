from scrapy.spiders import SitemapSpider

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class StratcoAUSpider(SitemapSpider, StructuredDataSpider, CamoufoxSpider):
    name = "stratco_au"
    item_attributes = {"brand": "Stratco", "brand_wikidata": "Q126179800", "country": "AU"}
    sitemap_urls = ["https://www.stratco.com.au/sitemap.xml"]
    sitemap_rules = [(r"/stores/(?!all-stores/?$)[^/]+/$", "parse_sd")]
    # The site sits behind a Cloudflare managed challenge that blocks the plain Scrapy downloader.
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS
    # The site uses a non-standard "HardwareStore" JSON-LD type instead of a schema.org standard type.
    wanted_types = ["HardwareStore"]
    # Every store shares the same generic brand logo image and brand-level social profiles.
    drop_attributes = {"image", "twitter", "facebook"}
    # National customer service hotline, repeated identically on most stores' pages
    # (formatted inconsistently as either "1300 165 165" or "1300165165").
    GENERIC_PHONE = "1300165165"

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["branch"] = item.pop("name")
        item["name"] = self.item_attributes["brand"]
        if item.get("phone") and item["phone"].replace(" ", "") == self.GENERIC_PHONE:
            item["phone"] = None
        apply_category(Categories.SHOP_HARDWARE, item)
        yield item
