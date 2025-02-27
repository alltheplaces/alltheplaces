from typing import Iterable

from scrapy.http import Response

from locations.categories import Extras, apply_yes_no
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class KahveDunyasiSpider(JSONBlobSpider):
    name = "kahve_dunyasi"
    start_urls = ["https://api.kahvedunyasi.com/api/v1/pim/store"]
    item_attributes = {"brand": "Kahve Dünyası", "brand_wikidata": "Q28008050"}
    locations_key = "payload"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature.get("latitute") and not feature.get("address"):
            return
        item["street_address"] = item.pop("addr_full", "")
        apply_yes_no(Extras.WIFI, item, feature["hasWifi"])
        apply_yes_no(Extras.TAKEAWAY, item, feature["isAvailableForTakeAway"])
        apply_yes_no(Extras.SMOKING_AREA, item, feature["hasSmokingArea"])
        apply_yes_no("parking", item, feature["hasCarPark"])
        # Opening hours don't match with Google Maps data, hence are not reliable.
        yield item
