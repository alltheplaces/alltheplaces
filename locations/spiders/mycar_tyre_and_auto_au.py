from scrapy.spiders import SitemapSpider

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, apply_category
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS
from locations.structured_data_spider import StructuredDataSpider


class MycarTyreAndAutoAUSpider(SitemapSpider, StructuredDataSpider, CamoufoxSpider):
    name = "mycar_tyre_and_auto_au"
    item_attributes = {
        "brand": "mycar Tyre & Auto",
        "brand_wikidata": "Q106224674",
    }
    allowed_domains = ["www.mycar.com.au"]
    sitemap_urls = ["https://www.mycar.com.au/sitemap.xml"]
    sitemap_rules = [(r"^https:\/\/www\.mycar\.com\.au\/stores\/\w+\/(?:(?<!closed-)[\w\-](?!-closed))+$", "parse_sd")]
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS

    def post_process_item(self, item, response, ld_data):
        item.pop("facebook", None)  # Brand-specific not location-specific.
        apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
