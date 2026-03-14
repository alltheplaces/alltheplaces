from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class MassachusettsDepartmentOfTransportationCulvertsUSSpider(ArcGISFeatureServerSpider):
    name = "massachusetts_department_of_transportation_culverts_us"
    item_attributes = {
        "operator": "Massachusetts Department of Transportation",
        "operator_wikidata": "Q2483364",
        "state": "MA",
        "nsi_id": "N/A",
    }
    host = "gis.massdot.state.ma.us"
    context_path = "arcgis"
    service_id = "Assets/Culverts"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["AssetID"]
        item["city"] = feature["Town_txt"]
        apply_category(Categories.CULVERT, item)
        if height_in := feature["height"]:
            item["extras"]["height"] = f'{height_in}"'
        if width_in := feature["width"]:
            item["extras"]["width"] = f'{width_in}"'
        if length_in := feature["length"]:
            item["extras"]["length"] = f'{length_in}"'
        yield item
