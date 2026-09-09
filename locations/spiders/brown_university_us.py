from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BrownUniversityUSSpider(ArcGISFeatureServerSpider):
    name = "brown_university_us"
    item_attributes = {"operator": "Brown University", "operator_wikidata": "Q49114", "state": "RI"}
    host = "services1.arcgis.com"
    context_path = "HMLBxPKXzqtpFXfq/ArcGIS"
    service_id = "Active_Buildings_2_view"
    layer_id = "0"
    # Excludes a lone parking structure sharing this layer, and a handful of
    # "Pre-active" records (sheds/dugouts/press boxes tied to sports fields
    # that aren't yet in active use) that aren't distinct mappable buildings.
    where_query = "Property_Type = 'Building' AND Property_Status = 'Active'"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("geometry", None)
        item["lat"] = feature["lat"]
        item["lon"] = feature["lon"]
        item["ref"] = feature["Property_Code"]
        item["name"] = feature["Property_Name"]
        item["street_address"] = feature["Address_Line_1"]
        item["city"] = "Providence"
        item["postcode"] = feature["ZIP_code"]
        apply_category(Categories.UNIVERSITY, item)
        yield item
