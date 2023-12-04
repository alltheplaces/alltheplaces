from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.storefinders.amrest_eu import AmrestEUSpider

YES_NO_ATTRIBUTES = {
    "garden": Extras.OUTDOOR_SEATING,
    "wifi": Extras.WIFI,
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
        for f in feature["filters"]:
            if tags := YES_NO_ATTRIBUTES.get(f["key"]):
                apply_yes_no(tags, item, f.get("available"))

            if f["key"] == "waiter_service":
                apply_category(Categories.RESTAURANT if f.get("available") else Categories.FAST_FOOD, item)
        yield item
