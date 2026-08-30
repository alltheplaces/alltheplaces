from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CaDmvUSSpider(ArcGISFeatureServerSpider):
    name = "ca_dmv_us"
    item_attributes = {
        "operator": "California Department of Motor Vehicles",
        "operator_wikidata": "Q5020431",
        "name": "California DMV",
        "state": "CA",
        "country": "US",
    }
    host = "services6.arcgis.com"
    context_path = "8zbIxywG5xu2vq8a/arcgis"
    service_id = "Department_of_Motor_Vehicles_Office_Locations"
    layer_id = "0"

    def pre_process_data(self, feature: dict) -> None:
        if address := feature.get("Address"):
            feature["Address"] = address.replace("\n", ", ")

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["FAC_ID"]
        item["branch"] = item.pop("name")
        apply_category(Categories.OFFICE_GOVERNMENT, item)
        yield item
