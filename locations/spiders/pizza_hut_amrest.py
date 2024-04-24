from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.amrest_eu import AmrestEUSpider

YES_NO_ATTRIBUTES = {
    "garden": Extras.OUTDOOR_SEATING,
    "wifi": Extras.WIFI,
    "driveThru": Extras.DRIVE_THROUGH,
}


class PizzaHutAmrestSpider(AmrestEUSpider):
    name = "pizza_hut_amrest"
    item_attributes = {"brand": "Pizza Hut", "brand_wikidata": "Q191615"}
    base_urls = [
        "https://api.amrest.eu/amdv/ordering-api/PH_PL/",
        "https://api.amrest.eu/amdv/ordering-api/PH_HU/",
        "https://api.amrest.eu/amdv/ordering-api/PH_CZ/",
    ]
    base_headers = AmrestEUSpider.base_headers | {"brand": "PH"}
    auth_data = AmrestEUSpider.auth_data | {"source": "WEB_PH"}

    def parse_item(self, item, feature, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Pizza Hut ")
        for f in feature["filters"]:
            if tags := YES_NO_ATTRIBUTES.get(f["key"]):
                apply_yes_no(tags, item, f.get("available"))

            if f["key"] == "waiter_service":
                if f.get("available"):
                    apply_category(Categories.RESTAURANT, item)
                else:
                    item["name"] = "Pizza Hut Express"
                    apply_category(Categories.FAST_FOOD, item)
        yield item
