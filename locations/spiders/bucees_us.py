from html import unescape
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Fuel, apply_yes_no
from locations.hours import DAYS_EN
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class BuceesUSSpider(WPStoreLocatorSpider):
    name = "bucees_us"
    item_attributes = {"brand": "Buc-ee's", "brand_wikidata": "Q4982335", "extras": Categories.FUEL_STATION.value}
    allowed_domains = ["buc-ees.com"]
    days = DAYS_EN
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = unescape("name")

        apply_yes_no(Fuel.DIESEL, item, True)
        apply_yes_no("car_wash", item, "carwash" in feature["terms"])

        apply_yes_no(Fuel.OCTANE_87, item, "87" in feature["octane_level"])
        apply_yes_no(Fuel.OCTANE_90, item, "90" in feature["octane_level"])
        apply_yes_no(Fuel.OCTANE_92, item, "92" in feature["octane_level"])
        apply_yes_no(Fuel.OCTANE_93, item, "93" in feature["octane_level"])

        apply_yes_no(Fuel.ADBLUE, item, "def-at-pump" in feature["terms"])
        apply_yes_no("fuel:ethanol_free", item, "ethanol-free" in feature["terms"])

        yield item
