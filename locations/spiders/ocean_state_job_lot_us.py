from typing import Iterable

from scrapy.http import TextResponse

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class OceanStateJobLotUSSpider(JSONBlobSpider):
    name = "ocean_state_job_lot_us"
    item_attributes = {"brand": "Ocean State Job Lot", "brand_wikidata": "Q7076076"}
    start_urls = [
        "https://www.oceanstatejoblot.com/api/commerce/storefront/locationUsageTypes/SP/locations/?pageSize=200&includeAttributeDefinition=true"
    ]
    locations_key = "items"

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["city"] = feature.get("address").get("cityOrTown")
        item["state"] = feature.get("address").get("stateOrProvince")
        item["postcode"] = feature.get("address").get("postalOrZipCode")
        item["ref"] = feature.get("code")
        yield item
