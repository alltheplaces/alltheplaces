import re

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class PetrolBGSpider(AgileStoreLocatorSpider):
    name = "petrol_bg"
    item_attributes = {"brand": "Petrol", "brand_wikidata": "Q24315"}
    allowed_domains = ["www.petrol.bg"]

    def parse_item(self, item, location):
        if m := re.match(r"^(\d+) (.+)$", item["name"]):
            item["ref"] = m.group(1)
            item["name"] = m.group(2)

        categories = (location["categories"] or "").split(",")
        if "31" in categories:
            charging_station_item = item.deepcopy()
            charging_station_item["ref"] = item.get("ref") + "-charging-station"
            charging_station_item["name"] = None
            charging_station_item["phone"] = None
            charging_station_item["opening_hours"] = None
            apply_category(Categories.CHARGING_STATION, charging_station_item)
            yield charging_station_item

        apply_yes_no(Fuel.DIESEL, item, ("19" in categories or "20" in categories))
        apply_yes_no(Fuel.OCTANE_100, item, "21" in categories)
        apply_yes_no(Fuel.OCTANE_95, item, "22" in categories)
        apply_yes_no(Fuel.LPG, item, "23" in categories)
        apply_yes_no(Fuel.CNG, item, "24" in categories)
        apply_yes_no(Extras.CAR_WASH, item, "25" in categories)
        apply_yes_no(Extras.ATM, item, "26" in categories)
        apply_yes_no("cafe", item, "27" in categories)
        apply_yes_no("self_service", item, "28" in categories)
        apply_yes_no(Fuel.ADBLUE, item, "29" in categories)

        yield item
