from copy import deepcopy
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiDKSESpider(JSONBlobSpider):
    name = "mitsubishi_dk_se"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = [
        f"https://mitsubishi-motors.{country_code}/wp-admin/admin-ajax.php?action=asl_load_stores"
        for country_code in ["dk", "se"]
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street", None)
        if website := feature.get("website"):
            item["website"] = "https://" + website if website.startswith("www.") else website

        categories = (feature.get("categories") or "").split(",")
        has_shop = "1" in categories or "19" in categories
        has_repair = "2" in categories or "18" in categories

        if has_shop:
            shop_item = deepcopy(item)
            shop_item["ref"] = f"{item['ref']}-shop"
            apply_category(Categories.SHOP_CAR, shop_item)
            apply_yes_no(Extras.CAR_REPAIR, shop_item, has_repair)
            yield shop_item

        if has_repair:
            repair_item = deepcopy(item)
            repair_item["ref"] = f"{item['ref']}-repair"
            apply_category(Categories.SHOP_CAR_REPAIR, repair_item)
            yield repair_item
