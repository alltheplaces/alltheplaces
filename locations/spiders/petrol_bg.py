import re

from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider
from locations.categories import Categories, Fuel, Extras

class PetrolBGSpider(AgileStoreLocatorSpider):
    name = "petrol_bg"
    item_attributes = {"brand": "Petrol", "brand_wikidata": "Q24315"}
    allowed_domains = ["www.petrol.bg"]

    def parse_item(self, item, location):
        if m := re.match(r"^(\d+) (.+)$", item["name"]):
            item["ref"] = m.group(1)
            item["name"] = m.group(2)
        
        categories = location["categories"].split(",")
        apply_yes_no(Fuel.DIESEL, item, ("19" in categories || "20" in categories))
        apply_yes_no(Fuel.OCTANE_100, item, "21" in categories)
        apply_yes_no(Fuel.OCTANE_95, item, "22" in categories)
        apply_yes_no(Fuel.LPG, item, "23" in categories)
        apply_yes_no(Fuel.CNG, item, "24" in categories)
        apply_yes_no(Extras.CAR_WASH, item, "25" in categories)
        apply_yes_no(Extras.ATM, item, "26" in categories)
        apply_yes_no("restaurant", item, "27" in categories)
        apply_yes_no("self_service", item, "28" in categories)
        apply_yes_no(Fuel.ADBLUE, item, "29" in categories)
        apply_yes_no("amenity:chargingstation", item, "31" in categories)
        
        yield item
