from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CityOfDublinCulvertsUSSpider(ArcGISFeatureServerSpider):
    name = "city_of_dublin_culverts_us"
    item_attributes = {
        "operator": "City of Dublin",
        "operator_wikidata": "Q111367157",
        "state": "OH",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "NqY8dnPSEdMJhuRw/arcgis"
    service_id = "Culverts"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["FacilityID"]
        apply_category(Categories.CULVERT, item)
        if width_ft := feature["Span"]:
            item["extras"]["width"] = f"{width_ft}'"
        if length_ft := feature["Length"]:
            item["extras"]["length"] = f"{length_ft}'"
        yield item
