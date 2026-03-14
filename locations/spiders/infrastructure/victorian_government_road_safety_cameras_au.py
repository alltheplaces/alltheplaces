from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class VictorianGovernmentRoadSafetyCamerasAUSpider(JSONBlobSpider):
    name = "victorian_government_road_safety_cameras_au"
    item_attributes = {"operator": "Department of Justice and Community Safety", "operator_wikidata": "Q5260361"}
    allowed_domains = ["www.vic.gov.au"]
    start_urls = ["https://www.vic.gov.au/api/tide/elasticsearch/sdp_data_pipelines_scl/_search?size=10000"]
    locations_key = ["hits", "hits"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("_source"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["camera_id"]
        item["addr_full"] = feature["offence_location"]
        item["state"] = "VIC"
        apply_category({"highway": "speed_camera"}, item)
        if feature["site_type"] == "Intersection":
            apply_category(Categories.ENFORCEMENT_MAXIMUM_SPEED, item)
            apply_category(Categories.ENFORCEMENT_TRAFFIC_SIGNALS, item)
        elif feature["site_type"] in ["Highway", "Freeway"]:
            apply_category(Categories.ENFORCEMENT_MAXIMUM_SPEED, item)
        elif feature["site_type"] == "Point-to-point":
            apply_category(Categories.ENFORCEMENT_AVERAGE_SPEED, item)
        yield item
