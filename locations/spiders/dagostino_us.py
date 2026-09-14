from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.instacart_connected_stores import InstacartConnectedStoresSpider


class DagostinoUSSpider(InstacartConnectedStoresSpider):
    name = "dagostino_us"
    item_attributes = {
        "brand_wikidata": "Q20656844",
        "brand": "D'Agostino",
    }
    storefront_root = "https://order.dagnyc.com"
    retailer_slug = "dagnyc"
    # D'Agostino operates only within Manhattan. A single, centrally located seed point was found
    # (2026-08) to return all locations even when queried from the opposite end of the island, but
    # a few extra seed points spread around the borough are used here as a hedge in case the
    # search radius used by the upstream API changes in the future.
    search_points = [
        ("10014", 40.733698, -74.007033),  # Greenwich Village
        ("10021", 40.7692, -73.9596),  # Upper East Side
        ("10024", 40.7870, -73.9754),  # Upper West Side
        ("10032", 40.8417, -73.9393),  # Washington Heights
    ]

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        name = item.pop("name", None) or ""
        item["branch"] = name.removeprefix("D'Agostino at ").strip()

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
