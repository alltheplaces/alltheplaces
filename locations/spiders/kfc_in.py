from typing import Iterable

from scrapy import Selector
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.spiders.kfc_us import KFC_SHARED_ATTRIBUTES
from locations.structured_data_spider import StructuredDataSpider


class KfcINSpider(SitemapSpider, StructuredDataSpider):
    name = "kfc_in"
    item_attributes = KFC_SHARED_ATTRIBUTES
    sitemap_urls = ["https://restaurants.kfc.co.in/robots.txt"]
    sitemap_rules = [(r"/kfc-[-\w]+-(\d+)/Home", "parse_sd")]
    time_format = "%I:%M %p"
    drop_attributes = {"image", "facebook"}
    wanted_types = ["LocalBusiness"]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        # city and state values are not correct, better to collect them to form addr_full
        item["addr_full"] = merge_address_lines(
            [item.pop("street_address"), item.pop("city"), item.pop("state"), item["postcode"]]
        )
        apply_category(Categories.FAST_FOOD, item)
        yield item

    def extract_amenity_features(self, item: Feature | dict, selector: Selector, ld_item: dict) -> None:
        services_list = []
        for services in ld_item.get("amenityFeature", []):
            if isinstance(services["value"], list):
                services_info = services["value"][0]
                if "," in services_info:
                    for service in services_info.split(","):
                        services_list.append(service.strip())
                else:
                    services_list.append(services_info)
        apply_yes_no(Extras.INDOOR_SEATING, item, "Dine In" in services_list)
        apply_yes_no(Extras.DELIVERY, item, "Delivery" in services_list)
        apply_yes_no(Extras.TAKEAWAY, item, "Takeaway" in services_list)
