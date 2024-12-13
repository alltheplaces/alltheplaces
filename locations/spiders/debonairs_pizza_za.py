from locations.categories import Extras, apply_yes_no
from locations.storefinders.yext_search import YextSearchSpider

DEBONAIRS_SHARED_ATTRIBUTES = {"brand": "Debonairs Pizza", "brand_wikidata": "Q65079407"}


class DebonairsPizzaZASpider(YextSearchSpider):
    name = "debonairs_pizza_za"
    item_attributes = DEBONAIRS_SHARED_ATTRIBUTES
    host = "https://location.debonairspizza.co.za"

    def parse_item(self, location, item):
        if "c_debonairsPizzaLocatorFilters" in location["profile"]:
            apply_yes_no(Extras.HALAL, item, "Halaal" in location["profile"]["c_debonairsPizzaLocatorFilters"])
            apply_yes_no(Extras.TAKEAWAY, item, "Takeaway" in location["profile"]["c_debonairsPizzaLocatorFilters"])
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in location["profile"]["c_debonairsPizzaLocatorFilters"])
        item["website"] = location["profile"]["c_pagesURL"]
        yield item
