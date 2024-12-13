from locations.categories import Extras, apply_yes_no
from locations.pipelines.address_clean_up import clean_address
from locations.storefinders.yext_search import YextSearchSpider

KNOWN_FUEL_STATIONS = ["Engen", "Sasol", "Shell", "Total"]
STEERS_FILTERS = {
    "Halaal": Extras.HALAL,
    "Generator": Extras.BACKUP_GENERATOR,
    "Drive Thru": Extras.DRIVE_THROUGH,
}


class SteersZASpider(YextSearchSpider):
    name = "steers_za"
    item_attributes = {"brand": "Steers", "brand_wikidata": "Q3056765"}
    host = "https://location.steers.co.za"

    def parse_item(self, location, item):
        apply_yes_no(Extras.DELIVERY, item, location["profile"].get("c_delivery"), False)

        if location_filters := location["profile"].get("c_steersLocatorFilters"):
            for filter, attribute in STEERS_FILTERS.items():
                apply_yes_no(attribute, item, filter in location_filters, False)

        if item["email"] == "info@steers.co.za":
            item.pop("email")

        street_address = item["street_address"]
        if item["branch"] in street_address:
            street_address = clean_address(street_address.replace(item["branch"], ""))
        if "," in street_address and any([fuel in street_address.split(",")[0] for fuel in KNOWN_FUEL_STATIONS]):
            street_address = clean_address(street_address.split(",", 1)[1])

        try:
            if " " in street_address:
                int(street_address.split(" ")[0])
                item["housenumber"] = street_address.split(" ", 1)[0]
                item["street"] = street_address.split(",")[0].split(" ", 1)[1]
        except ValueError:
            if not any([i in street_address for i in [",", "Corner", "Cnr", "c/o", "Portion"]]):
                item["street"] = street_address

        yield item
