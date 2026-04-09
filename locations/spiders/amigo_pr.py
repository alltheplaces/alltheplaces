from locations.categories import Categories
from locations.storefinders.elfsight import ElfsightSpider


class AmigoPRSpider(ElfsightSpider):
    name = "amigo_pr"
    item_attributes = {
        "brand": "Amigo",
        "brand_wikidata": "Q4746234",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    host = "core.service.elfsight.com"
    api_key = "5ffee2a7-32be-4ca7-8809-cec5d0a2e06f"

    def pre_process_data(self, feature: dict) -> None:
        if coordinates := feature.get("coordinates"):
            feature["coordinates"] = str(coordinates).replace(" ", ", ", 1)
        super().pre_process_data(feature)
