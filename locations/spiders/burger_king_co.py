from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingCOSpider(JSONBlobSpider):
    name = "burger_king_co"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    # Stores share a global id space across all Tillster tenants, so scan the
    # block covering "bk-co" and keep only that tenant's outlets.
    # The current bk-co block ids 96-138, scan a little beyond for future store additions.
    start_urls = [
        f"https://api.bk.com.co/mobilem8-web-service/rest/storeinfo/store/{store_id}?tenant=bk-co"
        for store_id in range(96, 150)
    ]

    def extract_json(self, response: TextResponse) -> list[dict]:
        store = response.json().get("getStoreResult", {}).get("store")
        if store.get("tenantId") != "bk-co" or store.get("storeName") == "GENERIC":
            return []
        return [store]

    def post_process_item(self, item: Feature, response: TextResponse, store: dict) -> Iterable[Feature]:
        item["ref"] = item.pop("name").split("-")[-1]
        item["phone"] = None
        item["street_address"] = item.pop("street")
        item["postcode"] = str(item["postcode"])
        properties = {p["propertyKey"]: p["propertyValue"] for p in store.get("storeProperties", [])}
        item["branch"] = properties.get("alias", "").removeprefix("BK ")
        item["lat"] = store["coordinate"]["lat"]
        item["lon"] = store["coordinate"]["lng"]
        apply_category(Categories.FAST_FOOD, item)

        yield item
