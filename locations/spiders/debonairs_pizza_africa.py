from locations.categories import Extras, apply_yes_no
from locations.storefinders.yext_search import YextSearchSpider


class DebonairsPizzaAfricaSpider(YextSearchSpider):
    name = "debonairs_pizza_africa"
    item_attributes = {"brand": "Debonairs Pizza", "brand_wikidata": "Q65079407"}
    host = "https://location.debonairspizza.africa"

    def parse_item(self, location, item):
        item["branch"] = location["profile"].get("geomodifier")
        item["extras"]["website:menu"] = location["profile"].get("menuUrl")
        if "c_debonairsPizzaLocatorFilters" in location["profile"]:
            apply_yes_no(Extras.HALAL, item, "Halaal" in location["profile"]["c_debonairsPizzaLocatorFilters"])
            apply_yes_no(Extras.TAKEAWAY, item, "Takeaway" in location["profile"]["c_debonairsPizzaLocatorFilters"])
            apply_yes_no(Extras.DELIVERY, item, "Delivery" in location["profile"]["c_debonairsPizzaLocatorFilters"])
        item["website"] = location["profile"]["c_pagesURL"]
        yield item
