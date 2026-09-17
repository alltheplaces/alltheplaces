from typing import Any

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.groupe_bertrand import GroupeBertrandSpider


class HippopotamusFRSpider(GroupeBertrandSpider):
    name = "hippopotamus_fr"
    item_attributes = {
        "brand": "Hippopotamus",
        "brand_wikidata": "Q3136174",
        "name": "Hippopotamus",
    }
    sitemap_urls = ["https://www.hippopotamus.fr/sitemap.xml"]
    sitemap_rules = [(r"/nos-restaurants/hippopotamus-", "parse")]

    def post_process_item(self, item: Feature, store: dict, raw_name: str) -> Any:
        item["branch"] = raw_name.removeprefix("Hippopotamus ")
        apply_category(Categories.RESTAURANT, item)
        yield item
