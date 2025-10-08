from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class KentuckyTransportationCabinetUSSpider(ArcGISFeatureServerSpider):
    name = "kentucky_transportation_cabinet_us"
    item_attributes = {"operator": "Kentucky Transportation Cabinet", "operator_wikidata": "Q4926022"}
    host = "services2.arcgis.com"
    context_path = "CcI36Pduqd0OR4W9/ArcGIS"
    service_id = "trafficCamerasCur_Prd"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        item["name"] = feature["description"]
        item["state"] = "KY"
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        item["extras"]["contact:webcam"] = feature["snapshot"]
        item["extras"]["camera:type"] = "fixed"
        yield item
