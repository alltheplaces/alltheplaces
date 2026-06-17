import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class TransportDepartmentTrafficCamerasHKSpider(ArcGISFeatureServerSpider):
    dataset_attributes = {
        "attribution": "required",
        "attribution:name": "Transport Department/Government of Hong Kong via CSDI Portal",
        "attribution:website": "https://portal.csdi.gov.hk/geoportal/?lang=en&datasetId=td_rcd_1638952287148_39267",
        "license": "Terms and Conditions of Use of the CSDI Portal",
        "license:website": "https://portal.csdi.gov.hk/csdi-webpage/doc/TNC",
        "use:commercial": "permit",
    }
    name = "transport_department_traffic_cameras_hk"
    item_attributes = {"operator": "運輸署 Transport Department", "operator_wikidata": "Q2355889"}
    host = "portal.csdi.gov.hk"
    context_path = "server"
    service_id = "common/td_rcd_1638952287148_39267"
    layer_id = "0"
    cam_name_regex = re.compile(r"(^.*)(?: \[.*].*$)")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        name = self.cam_name_regex.match(feature["description"])
        if name is None:
            self.logger.warning("Name not found for camera: {}".format(feature["key_"]))
        else:
            item["name"] = name.group(1)
        item["ref"] = feature["key_"]
        item["extras"]["contact:webcam"] = feature["url"]
        yield item
