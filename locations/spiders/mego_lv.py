from typing import Iterable

from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MegoLVSpider(JSONBlobSpider):
    name = "mego_lv"
    start_urls = ["https://mego.lv/wp-admin/admin-ajax.php?action=store_filter"]
    item_attributes = {"brand_wikidata": "Q16363314"}

    def extract_json(self, response: Response) -> list[dict]:
        stores = []
        for stores_data in response.json()["data"].values():
            stores.extend(stores_data["stores"])
        return stores

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("mapLocation", {}))
        feature["name"] = "Mego"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if hours := feature.get("information"):
            hours = hours.replace("Darba dienās", "Weekdays").replace("Sest.", "Sat.").replace("Sv.", "Sun.")
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours)
        yield item
