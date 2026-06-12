from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class YesparkSpider(SitemapSpider, StructuredDataSpider):
    name = "yespark"
    item_attributes = {"brand": "Yespark", "brand_wikidata": "Q109046724"}
    sitemap_urls = [
        "https://www.yespark.fr/sitemap/parkings.xml",
    ]
    sitemap_rules = [(r"/parkings/(\d+)-[-\w]+/?$", "parse_sd")]  # capture parking_id as reference
    wanted_types = ["ParkingFacility"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        apply_category(Categories.PARKING, item)
        apply_yes_no("fee", item, ld_data.get("isAccessibleForFree") is False, apply_positive_only=True)
        yield item

    def extract_amenity_features(self, item: Feature | dict, selector: Selector, ld_item: dict) -> None:
        for service in ld_item.get("amenityFeature", []):
            if service["name"].lower() == "underground parking" and service["value"] is True:
                item["extras"]["parking"] = "underground"
            elif service["name"].lower() == "cctv surveillance":
                apply_yes_no("surveillance", item, service["value"])
            elif service["name"].lower() == "electric vehicle charging":
                apply_yes_no(Fuel.ELECTRIC, item, service["value"])
