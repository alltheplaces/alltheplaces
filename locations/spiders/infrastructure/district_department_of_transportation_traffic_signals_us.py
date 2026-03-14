from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class DistrictDepartmentOfTransportationTrafficSignalsUSSpider(ArcGISFeatureServerSpider):
    name = "district_department_of_transportation_traffic_signals_us"
    item_attributes = {
        "operator": "District Department of Transportation",
        "operator_wikidata": "Q4923837",
        "state": "DC",
    }
    host = "maps2.dcgis.dc.gov"
    context_path = "dcgis"
    service_id = "DCGIS_DATA/Transportation_Signs_Signals_Lights_WebMercator"
    server_type = "MapServer"
    layer_id = "170"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["INTERSECTIONID"]
        item["name"] = feature["INTERSECTIONNAME"]
        apply_category(Categories.HIGHWAY_TRAFFIC_SIGNALS, item)
        yield item
