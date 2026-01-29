from typing import Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class BenAndJerrysSpider(Where2GetItSpider):
    name = "ben_and_jerrys"
    item_attributes = {"brand": "Ben & Jerry's", "brand_wikidata": "Q816412"}
    api_key = "3D71930E-EC80-11E6-A0AE-8347407E493E"
    api_filter = {"icon": {"in": "default,SHOP"}}
    api_brand_name = "benjerry"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        # Appears to be an indicator for suppliers (not actual shops), even after api_filter above
        if location.get("jsonshopinfo") is None:  # May be equivalent to "jsonshop"
            return
        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]

        item["branch"] = item.pop("name").replace(self.item_attributes["brand"], "").strip()
        apply_category(Categories.ICE_CREAM, item)

        apply_yes_no(Extras.DELIVERY, item, location["offersdelivery"] == "1")

        item["opening_hours"] = OpeningHours()
        for day in DAYS_FULL:
            if location.get(day.lower()) in [None, ""]:
                continue
            if "closed" in location.get(day.lower()):
                item["opening_hours"].set_closed(day)
            else:
                item["opening_hours"].add_ranges_from_string(day + " " + location.get(day.lower()))

        yield item
