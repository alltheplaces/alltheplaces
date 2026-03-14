from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class PetrocityKEUGSpider(WPStoreLocatorSpider):
    name = "petrocity_ke_ug"
    item_attributes = {"brand": "Petrocity", "brand_wikidata": "Q134958497"}
    allowed_domains = ["petrocityafrica.com"]
    days = DAYS_EN

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = feature["store"].removesuffix(" Service Station").removesuffix(" Station")
        item.pop("name", None)
        item["addr_full"] = merge_address_lines([feature["address"], feature["address2"]])
        item.pop("street_address", None)
        apply_category(Categories.FUEL_STATION, item)
        yield item
