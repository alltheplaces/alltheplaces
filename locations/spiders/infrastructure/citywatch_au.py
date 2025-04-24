from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CitywatchAUSpider(ArcGISFeatureServerSpider):
    name = "citywatch_au"
    item_attributes = {"operator": "City of Perth", "operator_wikidata": "Q1855330"}
    host = "services7.arcgis.com"
    context_path = "v8XBa2naYNQGOjlG/ArcGIS"
    service_id = "INF_AST_SECURITYCAMERAS_PV"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["CAMERA_NUM"]
        item["state"] = "WA"
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        item["extras"]["surveillance"] = "public"
        yield item
