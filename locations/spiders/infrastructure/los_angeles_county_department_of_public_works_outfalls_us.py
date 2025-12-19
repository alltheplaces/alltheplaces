from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class LosAngelesCountyDepartmentOfPublicWorksOutfallsUSSpider(ArcGISFeatureServerSpider):
    name = "los_angeles_county_department_of_public_works_outfalls_us"
    item_attributes = {
        "operator": "Los Angeles County Department of Public Works",
        "operator_wikidata": "Q6682081",
        "state": "CA",
        "nsi_id": "N/A",
    }
    host = "dpw.gis.lacounty.gov"
    context_path = "dpw"
    service_id = "WaterResources"
    server_type = "MapServer"
    layer_id = "96"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["OUTFALL_ID"]
        apply_category(Categories.OUTFALL_STORMWATER, item)
        yield item
