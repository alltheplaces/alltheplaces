from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NorthDakotaDepartmentOfTransportationTrafficCamerasUSSpider(ArcGISFeatureServerSpider):
    name = "north_dakota_department_of_transportation_traffic_cameras_us"
    item_attributes = {"operator": "North Dakota Department of Transportation", "operator_wikidata": "Q5569030", "nsi_id": "N/A", "state": "ND"}
    host = "gis.dot.nd.gov"
    context_path = "arcgis"
    service_id = "external/rcrs_dynamic"
    server_type = "MapServer"
    layer_id = "5"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        images = list(filter(None, [feature.get("FullPath"), feature.get("FullPath2"), feature.get("FullPath3"), feature.get("FullPath4"), feature.get("FullPath5"), feature.get("FullPath6")]))
        item["extras"]["contact:webcam"] = ";".join(images)
        if len(images) > 2:
            item["extras"]["camera:type"] = "dome"
        else:
            item["extras"]["camera:type"] = "fixed"
        yield item
