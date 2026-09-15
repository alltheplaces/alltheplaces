from typing import Any

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.groupe_bertrand import GroupeBertrandSpider


class AubureauFRSpider(GroupeBertrandSpider):
    name = "aubureau_fr"
    item_attributes = {"brand": "Au Bureau", "brand_wikidata": "Q100701566", "name": "Au Bureau"}
    sitemap_urls = ["https://www.aubureau.fr/sitemap.xml"]
    sitemap_rules = [(r"/restaurant-brasserie/au-bureau-", "parse")]

    def post_process_item(self, item: Feature, store: dict, raw_name: str) -> Any:
        item["branch"] = raw_name.removeprefix("Au Bureau - ")
        apply_category(Categories.RESTAURANT, item)
        yield item
