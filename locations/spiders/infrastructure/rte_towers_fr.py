from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class RteTowersFRSpider(ArcGISFeatureServerSpider):
    name = "rte_towers_fr"
    item_attributes = {"operator": "RTE", "operator_wikidata": "Q2178795"}
    host = "services1.arcgis.com"
    context_path = "x2oYdXVT265NhFqt/ArcGIS"
    service_id = "Données_Open_DATA_et_GPU_Externe"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["OBJECTID"]
        item["name"] = feature["NOMOUVRAGE"]
        apply_category(Categories.POWER_TOWER, item)
        item["ref"] = feature["ID"] + "-" + feature["NUM_PYL"]
        yield item
