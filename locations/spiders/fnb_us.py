from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.yext import YextSpider


class FnbUSSpider(YextSpider):
    name = "fnb_us"
    item_attributes = {"brand": "First National Bank", "brand_wikidata": "Q5426765"}
    api_key = "10f82fdf7a37ee369b154241c59dade1"
    api_version = "20190101"
    wanted_types = ["location", "atm"]

    def parse_item(self, item, location, **kwargs):
        entity_type = location["meta"]["entityType"]
        if entity_type == "location":
            apply_category(Categories.BANK, item)
            apply_yes_no(
                Extras.ATM, item, any(s in ["ATM", "ATM with Teller Chat"] for s in location.get("c_branchFilters", []))
            )
            apply_yes_no(Extras.DRIVE_THROUGH, item, "Drive-Thru" in location.get("c_branchFilters", []))
        elif entity_type == "atm":
            apply_category(Categories.ATM, item)
        yield item
