from typing import Iterable

from locations.categories import Categories, Fuel, FuelCards, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.storepoint import StorepointSpider


class AlliedPetroleumNZSpider(StorepointSpider):
    name = "allied_petroleum_nz"
    item_attributes = {"brand": "Allied Petroleum", "brand_wikidata": "Q112543637"}
    key = "15f7a892408575"

    def parse_item(self, item: Feature, location: dict, **kwargs) -> Iterable[Feature]:
        if "Mobil" in (item.get("name") or ""):
            return
        if branch := item.pop("name", None):
            item["branch"] = (
                branch.replace("Fuel Stop", "")
                .replace("Fuelstop", "")
                .replace("Marine Stop", "")
                .replace("24/7", "")
                .replace("Service Station", "")
                .strip()
            )
        apply_category(Categories.FUEL_STATION, item)
        if "open 24/7" in location["tags"]:
            item["opening_hours"] = "24/7"
        if item["facebook"] == "0":
            item["facebook"] = ""
        if item["twitter"] == "0":
            item["twitter"] = ""
        apply_yes_no(Fuel.ADBLUE, item, "alliedblue" in location["tags"])
        apply_yes_no(Fuel.DIESEL, item, "diesel" in location["tags"])
        apply_yes_no(Fuel.OCTANE_91, item, "91 petrol" in location["tags"])
        apply_yes_no(Fuel.OCTANE_95, item, "95 petrol" in location["tags"])
        apply_yes_no(FuelCards.MOBIL, item, "mobilcard" in location["tags"])
        yield item
