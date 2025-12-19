from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BoiseCityDepartmentOfPublicWorksStreetLampsUSSpider(ArcGISFeatureServerSpider):
    name = "boise_city_department_of_public_works_street_lamps_us"
    item_attributes = {
        "operator": "Boise City Department of Public Works",
        "operator_wikidata": "Q133930333",
        "state": "ID",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "WHM6qC35aMtyAAlN/ArcGIS"
    service_id = "Boise_Streetlights_Open_Data"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["Department_ID"]
        item["street_address"] = feature["Location"]
        apply_category(Categories.STREET_LAMP, item)
        if height_ft := feature.get("Height"):
            item["extras"]["height"] = f"{height_ft}'"
        yield item
