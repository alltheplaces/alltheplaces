from typing import Any, Iterable

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BojanglesUSSpider(JSONBlobSpider):
    name = "bojangles_us"
    item_attributes = {"brand": "Bojangles'", "brand_wikidata": "Q891163"}
    start_urls = ["https://bojangles.com/unified-gateway/online-ordering/v1/all-stores/23446?limit=50"]
    locations_key = "stores_v1"

    def pre_process_data(self, feature: dict) -> None:
        address = feature.get("address", {})
        feature.update(address)
        feature["state"] = address.get("administrative_area_level1")

    def post_process_item(self, item: Feature, response: Any, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item["street_address"] = item.pop("street", None)
        apply_yes_no(Extras.DELIVERY, item, feature.get("offers_delivery"))
        apply_yes_no(Extras.TAKEAWAY, item, feature.get("offers_pickup"))
        apply_category(Categories.FAST_FOOD, item)
        yield item
