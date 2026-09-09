from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.burger_king import BURGER_KING_SHARED_ATTRIBUTES


class BurgerKingCOSpider(JSONBlobSpider):
    name = "burger_king_co"
    item_attributes = BURGER_KING_SHARED_ATTRIBUTES
    start_urls = [
        "https://api.bk.com.co/mobilem8-web-service/rest/storeinfo/distance?tenant=bk-co&latitude=4.65&longitude=-74.06&radius=5000&maxResults=500"
    ]
    locations_key = ["getStoresResult", "stores"]

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
