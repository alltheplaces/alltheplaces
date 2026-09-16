from typing import Any

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.groupe_bertrand import GroupeBertrandSpider


class LeonDeBruxellesFRSpider(GroupeBertrandSpider):
    name = "leon_de_bruxelles_fr"
    item_attributes = {"brand": "Léon de Bruxelles", "brand_wikidata": "Q21041507"}
    sitemap_urls = ["https://www.restaurantleon.fr/sitemap.xml"]
    sitemap_rules = [(r"/nos-restaurants/[^/]+$", "parse")]

    def post_process_item(self, item: Feature, store: dict, raw_name: str) -> Any:
        # raw_name is "<concept> - <city>", e.g. "Léon Seafood & Cocktails - Villeparisis"; the
        # concept prefix varies per store ("Léon Fish Brasserie", "Léon Restaurant", ...) so the
        # branch is whatever follows the separator, not a fixed brand-name prefix to strip.
        _, item["branch"] = raw_name.split(" - ", 1)
        if item.get("email") == "serviceclients@restaurantleon.fr":
            item["email"] = None

        apply_category(Categories.RESTAURANT, item)
        yield item
