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
        if feature.get("state") and isinstance(feature.get("state"), list):
            feature["state"] = feature["state"][0].get("name")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["phone"] = feature.get("office_number")
        item["email"] = feature.get("centre_email")
        item["extras"]["fax"] = feature.get("fax_number")
        item["image"] = feature.get("featured_img_url")

        services = feature.get("centre_type")

        if "showroom" in services:
            sales_item = item.deepcopy()
            sales_item["ref"] = "{}-sales".format(sales_item["ref"])
            apply_category(Categories.SHOP_CAR, sales_item)
            yield sales_item

        if "service" in services or "windscreen-replacement" in services:
            service_item = item.deepcopy()
            service_item["ref"] = "{}-service".format(service_item["ref"])
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            apply_yes_no(Extras.VEHICLE_WINDSCREEN_REPLACEMENT_SERVICES, item, "windscreen-replacement" in services)
            yield service_item

        if "parts-stockist" in services:
            parts_item = item.deepcopy()
            parts_item["ref"] = "{}-parts".format(service_item["ref"])
            apply_category(Categories.SHOP_CAR_PARTS, parts_item)
            yield parts_item

        if "body-paint" in services:
            painter_item = item.deepcopy()
            painter_item["ref"] = "{}-paint".format(painter_item["ref"])
            apply_category(Categories.CRAFT_CAR_PAINTER, painter_item)
            yield painter_item
