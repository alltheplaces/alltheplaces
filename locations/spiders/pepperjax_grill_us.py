from scrapy.spiders import SitemapSpider

from locations.categories import Categories, apply_category
from locations.structured_data_spider import StructuredDataSpider


class PepperjaxGrillUSSpider(SitemapSpider, StructuredDataSpider):
    name = "pepperjax_grill_us"
    item_attributes = {"name": "PepperJax Grill"}
    sitemap_urls = ["https://pepperjaxgrill.com/sitemap.xml"]
    sitemap_rules = [(r"^https://pepperjaxgrill\.com/[a-z]{2}/[^/]+/[^/]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        # Coordinates are published as flat "latitude"/"longitude" keys on the
        # FastFoodRestaurant node rather than the standard nested "geo" object.
        item["lat"] = ld_data.get("latitude")
        item["lon"] = ld_data.get("longitude")

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sandwich"

        yield item
