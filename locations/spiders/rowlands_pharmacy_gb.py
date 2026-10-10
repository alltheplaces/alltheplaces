from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class RowlandsPharmacyGBSpider(JSONBlobSpider):
    name = "rowlands_pharmacy_gb"
    item_attributes = {"brand": "Rowlands Pharmacy", "brand_wikidata": "Q62663235"}
    start_urls = ["https://shop-services.rowlandspharmacy.co.uk/pharmacy-tools/api/locations"]
    locations_key = "locations"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([item["street_address"], feature["address"]["addressLine2"]])

        item["opening_hours"] = OpeningHours()
        for day, intervals in feature["openIntervals"].items():
            if not intervals["openIntervals"]:
                item["opening_hours"].set_closed(day)
            for interval in intervals["openIntervals"]:
                item["opening_hours"].add_range(day, interval["start"], interval["end"])

        apply_category(Categories.PHARMACY, item)

        yield item
