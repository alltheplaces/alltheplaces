from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiMYSpider(JSONBlobSpider):
    name = "mitsubishi_my"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.com.my/wp-admin/admin-ajax.php?action=update_dealer_markers"]

    def pre_process_data(self, feature: dict) -> None:
        if isinstance(feature.get("state"), list):
            feature["state"] = feature["state"][0].get("name")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["phone"] = feature.get("office_number")
        item["email"] = feature.get("centre_email")
        item["extras"]["fax"] = feature.get("fax_number")
        item["image"] = feature.get("featured_img_url")

        services = feature.get("centre_type")
        if not services:  # Doesn't look a branded location
            return
        if "showroom" in services:
            apply_category(Categories.SHOP_CAR, item)
        elif "service" in services:
            apply_category(Categories.SHOP_CAR_REPAIR, item)
        elif services == ["parts-stockist"]:
            apply_category(Categories.SHOP_CAR_PARTS, item)
        elif services == ["body-paint"]:
            apply_category({"shop": "car_painting"}, item)
        apply_yes_no(Extras.CAR_PARTS, item, "parts-stockist" in services)
        apply_yes_no("service:vehicle:glass", item, "windscreen-replacement" in services)
        apply_yes_no("service:vehicle:painting", item, "body-paint" in services)
        yield item
