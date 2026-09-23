from typing import Any

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.groupe_bertrand import GroupeBertrandSpider


class LeParadisDuFruitFRSpider(GroupeBertrandSpider):
    name = "le_paradis_du_fruit_fr"
    item_attributes = {
        "brand": "Le Paradis du Fruit",
        "brand_wikidata": "Q109315292",
        "name": "Le Paradis du Fruit",
    }
    sitemap_urls = ["https://www.leparadisdufruit.fr/sitemap.xml"]
    sitemap_rules = [(r"/nos-restaurants/le-paradis-du-fruit-", "parse")]

    # publicEmail is set to this same customer-service hotline on most stores (~75% of them),
    # rather than a per-location address - drop it when seen instead of treating it as real data.
    GENERIC_EMAIL = "serviceclient.paradisdufruit@bertrand-franchise.com"

    def post_process_item(self, item: Feature, store: dict, raw_name: str) -> Any:
        item["branch"] = raw_name.removeprefix("Le Paradis du Fruit ")
        if item.get("email") == self.GENERIC_EMAIL:
            item["email"] = None
        apply_category(Categories.RESTAURANT, item)
        yield item
