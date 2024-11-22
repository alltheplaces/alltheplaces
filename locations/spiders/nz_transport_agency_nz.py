from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class NZTransportAgencyNZSpider(JSONBlobSpider):
    name = "nz_transport_agency_nz"
    item_attributes = {"operator": "NZ Transport Agency", "operator_wikidata": "Q7015807", "extras": Categories.SURVEILLANCE_CAMERA.value, "nsi_id": "N/A"}
    allowed_domains = ["www.journeys.nzta.govt.nz"]
    start_urls = ["https://www.journeys.nzta.govt.nz/assets/map-data-cache/cameras.json"]
    locations_key = "features"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature["properties"])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("ExternalId")
        item["extras"]["contact:webcam"] = feature.get("ImageUrl")
        item["extras"]["camera:type"] = "fixed"
        yield item
