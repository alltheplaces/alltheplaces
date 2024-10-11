from locations.categories import Extras, apply_yes_no
from locations.storefinders.yext_search import YextSearchSpider


class SteersZASpider(YextSearchSpider):
    name = "steers_za"
    item_attributes = {"brand": "Steers", "brand_wikidata": "Q3056765"}
    host = "https://location.steers.co.za"

    def parse_item(self, location, item):
        apply_yes_no(Extras.DELIVERY, item, location["profile"].get("c_delivery"), False)
        if location_filters := location.get("c_steersLocatorFilters"):
            apply_yes_no(Extras.HALAL, item, "Halaal" in location_filters, False)
            apply_yes_no(Extras.BACKUP_GENERATOR, item, "Generator" in location_filters, False)
        yield item
