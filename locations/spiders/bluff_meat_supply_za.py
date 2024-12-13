from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BluffMeatSupplyZASpider(WPStoreLocatorSpider):
    name = "bluff_meat_supply_za"
    item_attributes = {
        "brand": "Bluff Meat Supply",
        "brand_wikidata": "Q116981518",
    }
    allowed_domains = ["bluffmeatsupply.co.za"]

    def pre_process_data(self, feature: dict) -> None:
        feature["hours"] = feature.pop("address2").removeprefix("Operating Hours:")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("BMS", "").strip()
        item["addr_full"] = item.pop("street_address")
        item["opening_hours"] = OpeningHours()
        item["opening_hours"].add_ranges_from_string(feature["hours"])
        yield item
