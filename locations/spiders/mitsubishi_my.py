from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiMYSpider(JSONBlobSpider):
    name = "mitsubishi_my"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://www.mitsubishi-motors.com.my/wp-admin/admin-ajax.php?action=get_dealer_markers"]

    def pre_process_data(self, feature: dict) -> None:
        if isinstance(feature.get("state"), list):
            feature["state"] = feature["state"][0].get("name")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["phone"] = feature.get("office_number")
        item["email"] = feature.get("centre_email")
        item["extras"]["fax"] = feature.get("fax_number")
        item["image"] = feature.get("featured_img_url")
        yield item
