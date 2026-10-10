import re
from typing import Any

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.groupe_bertrand import GroupeBertrandSpider


class VolfoniFRSpider(GroupeBertrandSpider):
    name = "volfoni_fr"
    item_attributes = {"brand": "Volfoni", "brand_wikidata": "Q135725721", "name": "Volfoni"}
    sitemap_urls = ["https://www.volfoni.fr/sitemap.xml"]
    sitemap_rules = [(r"/nos-restaurants/volfoni-", "parse")]

    def post_process_item(self, item: Feature, store: dict, raw_name: str) -> Any:
        # Separator after "Volfoni" isn't consistent (space, hyphen, or en dash).
        item["branch"] = re.sub(r"^Volfoni[\s\-–]+", "", raw_name)
        # Shared complaints inbox, not a per-location address.
        if item.get("email") == "reclamation@groupebk.fr":
            item["email"] = None
        apply_category(Categories.RESTAURANT, item)
        yield item
