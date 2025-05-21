import re

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class EinsteinBrosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "einstein_bros_us"
    item_attributes = {"brand": "Einstein Bros. Bagels", "brand_wikidata": "Q5349788"}
    allowed_domains = ["einsteinbros.com"]
    sitemap_urls = ["https://locations.einsteinbros.com/sitemap.xml"]
    sitemap_rules = [(r"/us/[a-z]{2}/[-\w]+/[-\w]+$", "parse_sd")]
    coordinates_pattern = re.compile(r"%7B%22latitude%22%3A([-.\d]+)%2C%22longitude%22%3A([-.\d]+)%7D")

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        if coordinates := re.search(self.coordinates_pattern, response.text):
            item["lat"], item["lon"] = coordinates.groups()
        item["branch"] = item.pop("name").removeprefix("Einstein Bros. Bagels ")
        yield item

    def extract_amenity_features(self, item, response: Response, ld_item):
        features = [feature["name"] for feature in ld_item.get("amenityFeature") or []]
        apply_yes_no(Extras.WIFI, item, "WiFi" in features)
        apply_yes_no(Extras.INDOOR_SEATING, item, "Dine-In" in features)
        if "Takeout Only" in features:
            item["extras"]["takeaway"] = "only"
