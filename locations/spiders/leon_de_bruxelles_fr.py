from typing import Any

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.groupe_bertrand import GroupeBertrandSpider


class LeonDeBruxellesFRSpider(GroupeBertrandSpider):
    name = "leon_de_bruxelles_fr"
    item_attributes = {
        "brand": "Léon de Bruxelles",
        "brand_wikidata": "Q21041507",
        "name": "Léon de Bruxelles",
    }
    sitemap_urls = ["https://www.restaurantleon.fr/sitemap.xml"]
    sitemap_rules = [(r"/nos-restaurants/[^/]+$", "parse")]

    # publicEmail is set to this same customer-service hotline on almost every store (61/62),
    # rather than a per-location address - drop it when seen instead of treating it as real data.
    GENERIC_EMAIL = "serviceclients@restaurantleon.fr"

    def post_process_item(self, item: Feature, store: dict, raw_name: str) -> Any:
        # raw_name is "<concept> - <city>", e.g. "Léon Seafood & Cocktails - Villeparisis"; the
        # concept prefix varies per store ("Léon Fish Brasserie", "Léon Restaurant", ...) so the
        # branch is whatever follows the separator, not a fixed brand-name prefix to strip.
        item["branch"] = raw_name.split(" - ", 1)[-1]
        if item.get("email") == self.GENERIC_EMAIL:
            item["email"] = None
        apply_category(Categories.RESTAURANT, item)
        yield item
