from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.yext import YextSpider


class TheGoodFeetStoreSpider(YextSpider):
    name = "the_good_feet_store"
    item_attributes = {"brand": "The Good Feet Store", "brand_wikidata": "Q122031157"}
    api_key = "a066029e87b7dcbd3ae30028efc31e28"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        if not location.get("c_activeOnListings"):
            return
        if "COMING SOON" in location["c_officialStoreName"].upper():
            return
        item["branch"] = location["c_officialStoreName"]
        item.pop("name", None)
        item["website"] = location["c_pagesURL"]
        apply_category(Categories.SHOP_SHOES, item)
        item["extras"].pop("contact:instagram")
        if google_place_id := location.get("googlePlaceId"):
            item["extras"]["ref:google:place_id"] = google_place_id
        yield item
