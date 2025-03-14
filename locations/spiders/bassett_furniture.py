from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.storefinders.where2getit import Where2GetItSpider


class BassettFurnitureSpider(Where2GetItSpider):
    name = "bassett_furniture"
    item_attributes = {"brand": "Bassett Furniture", "brand_wikidata": "Q4868109"}
    api_endpoint = "https://stores.bassettfurniture.com/rest/getlist"
    api_key = "A605E3A0-6CA3-11EB-A657-F9FB92322438"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        if location["coming_soon"] == "1" or location["permclosed"] == "1":
            return
        if location["display_name"] == "Partner Store":
            return

        item["lat"] = location["latitude"]
        item["lon"] = location["longitude"]
        if len(location["links"]) > 0:
            item["website"] = location["links"][0]

        item["opening_hours"] = OpeningHours()
        for day_name in DAYS_FULL:
            open_time = location.get(day_name.lower() + "_open")
            close_time = location.get(day_name.lower() + "_close")
            if open_time and close_time:
                item["opening_hours"].add_range(day_name, open_time, close_time)
            else:
                item["opening_hours"].set_closed(day_name)

        apply_category(Categories.SHOP_FURNITURE, item)
        yield item
