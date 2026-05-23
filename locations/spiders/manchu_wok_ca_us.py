from typing import Iterable

from parsel import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class ManchuWokCAUSSpider(SuperStoreFinderSpider):
    name = "manchu_wok_ca_us"
    item_attributes = {
        "brand_wikidata": "Q6747622",
        "brand": "Manchu Wok",
    }
    allowed_domains = [
        "locations.manchuwok.com",
    ]

    def parse_item(self, item: Feature, location: Selector) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        apply_category(Categories.FAST_FOOD, item)
        yield item
