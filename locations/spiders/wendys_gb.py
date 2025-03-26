from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class WendysGBSpider(SitemapSpider, StructuredDataSpider):
    name = "wendys_gb"
    item_attributes = {"brand": "Wendy's", "brand_wikidata": "Q550258"}
    wanted_types = ["FastFoodRestaurant"]
    sitemap_urls = ["https://uklocations.wendys.com/sitemap.xml"]
    sitemap_rules = [(r"https://uklocations.wendys.com/.+/.+", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["name"] = item["image"] = None
        item["website"] = ld_data.get("url")

        yield item

    def extract_amenity_features(self, item, response: Response, ld_item):
        if isinstance(ld_item.get("amenityFeature"), str):
            ld_item["amenityFeature"] = [ld_item["amenityFeature"]]

        apply_yes_no(Extras.WIFI, item, "Wi-Fi" in ld_item.get("amenityFeature", []))
