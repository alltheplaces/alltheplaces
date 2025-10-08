from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfSydneyStreetSafetyCamerasAUSpider(ArcGISFeatureServerSpider):
    name = "city_of_sydney_street_safety_cameras_au"
    item_attributes = {"operator": "City of Sydney", "operator_wikidata": "Q56477532"}
    host = "services1.arcgis.com"
    context_path = "cNVyNtjGVZybOQWZ/ArcGIS"
    service_id = "CCTV_Locations"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["CAMERA_NO"])
        item["name"] = feature["Location"]
        item["state"] = "NSW"
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        item["extras"]["surveillance"] = "public"
        yield item
