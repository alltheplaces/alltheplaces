import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class VermontElectricCooperativeTransformersUSSpider(ArcGISFeatureServerSpider):
    name = "vermont_electric_cooperative_transformers_us"
    item_attributes = {"operator": "Vermont Electric Cooperative", "operator_wikidata": "Q7921713", "state": "VT", "nsi_id": "N/A"}
    host = "services6.arcgis.com"
    context_path = "xcyrEMQ4nxKC9P7Y/ArcGIS"
    service_id = "VEC_Online_Viewer"
    layer_id = "3"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        apply_category(Categories.TRANSFORMER, item)
        if capacity_kva := feature["gs_rated_kva"]:
            item["extras"]["rating"] = f"{capacity_kva} kVA"
        yield item
