from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class VermontElectricCooperativePolesUSSpider(ArcGISFeatureServerSpider):
    name = "vermont_electric_cooperative_poles_us"
    item_attributes = {
        "operator": "Vermont Electric Cooperative",
        "operator_wikidata": "Q7921713",
        "state": "VT",
        "nsi_id": "N/A",
    }
    host = "services6.arcgis.com"
    context_path = "xcyrEMQ4nxKC9P7Y/ArcGIS"
    service_id = "VEC_Online_Viewer"
    layer_id = "8"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["gs_facility_id"]
        apply_category(Categories.POWER_POLE, item)
        if height_ft := feature.get("gs_height"):
            item["extras"]["height"] = f"{height_ft}'"
        if feature.get("gs_year_manufactured") and feature.get("gs_year_manufactured") != "UNK":
            item["extras"]["start_date"] = feature["gs_year_manufactured"]
        yield item
