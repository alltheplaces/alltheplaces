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

        categories = (feature.get("categories") or "").split(",")
        if "1" in categories or "19" in categories:
            apply_category(Categories.SHOP_CAR, item)
            apply_yes_no(Extras.CAR_REPAIR, item, "2" in categories or "18" in categories)
        elif "2" in categories or "18" in categories:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        yield item
