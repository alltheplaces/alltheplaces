from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChickenTreatAUSpider(JSONBlobSpider):
    name = "chicken_treat_au"
    item_attributes = {"brand": "Chicken Treat", "brand_wikidata": "Q5096274"}
    start_urls = ["https://d3c377j0gjsips.cloudfront.net/ct_all_store_sync.json"]
    locations_key = "data"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("attributes"))
        if address := feature["relationships"].get("storeAddress"):
            for key, component in address["data"]["attributes"]["addressComponents"].items():
                feature[key] = (component or {}).get("value")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if not feature.get("isEnabledForTrading"):
            return
        if not feature.get("isCollectionEnabled") and not feature.get("isDeliveryEnabled"):
            return
        if not feature["relationships"].get("storeAddress"):  # closed stores have no address
            return

        item["branch"] = item.pop("name", None)
        item["street_address"] = item.pop("street", None)
        if feature.get("floor"):
            item["extras"]["addr:floor"] = feature["floor"]
        item["website"] = (
            "https://www.chickentreat.com.au/locations/"
            + feature["relationships"]["slug"]["data"]["attributes"]["slug"]
        )

        item["opening_hours"] = OpeningHours()
        for day_hours in feature["relationships"]["collection"]["data"]["attributes"]["collectionTimes"]:
            for period in day_hours["collectionTimePeriods"]:
                item["opening_hours"].add_range(
                    day_hours["dayOfWeek"], period["openTime"], period["closeTime"], "%H:%M:%S"
                )

        amenities = feature["relationships"]["amenities"]["data"]["attributes"]
        apply_yes_no(Extras.TOILETS, item, amenities["haveToilet"], False)
        apply_yes_no(Extras.WIFI, item, amenities["haveWifi"], False)
        apply_yes_no(Extras.DELIVERY, item, feature.get("isDeliveryEnabled"), False)
        apply_yes_no(Extras.TAKEAWAY, item, feature.get("isCollectionEnabled"), False)
        apply_category(Categories.FAST_FOOD, item)
        yield item
