from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BaptistHealthArkansasUSSpider(JSONBlobSpider):
    name = "baptist_health_arkansas_us"
    item_attributes = {
        "brand": "Baptist Health Foundation",
        "brand_wikidata": "Q50379824",
    }
    start_urls = [
        "https://api.loyalhealth.com/search/d89ae0b6-4b09-46a4-9b9c-1eb670fc80e6/1/search/locations?disabledEmployedRankings=false&showProviderIndex=true"
    ]
    locations_key = "locations"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["entityId"]
        item["website"] = f'https://www.baptist-health.org/find-location/location/{feature["displayUrl"]}'
        if facility_type := feature["locationType"][0].get("displayName"):
            if "Hospital" in facility_type:
                apply_category(Categories.HOSPITAL, item)
            elif "Urgent Care" in facility_type:
                apply_category(Categories.CLINIC_URGENT, item)
            else:
                apply_category(Categories.CLINIC, item)
        yield item
