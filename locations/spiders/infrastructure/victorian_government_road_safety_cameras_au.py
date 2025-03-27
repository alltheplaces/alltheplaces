from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class VictorianGovernmentRoadSafetyCamerasAUSpider(ArcGISFeatureServerSpider):
    name = "victorian_government_road_safety_cameras_au"
    item_attributes = {"operator": "Department of Justice and Community Safety", "operator_wikidata": "Q5260361"}
    host = "services-ap1.arcgis.com"
    context_path = "qP7JqzPTuwJlaCRD/ArcGIS"
    service_id = "road_safety_camera_network_data_v3"
    layer_id = "0"

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
