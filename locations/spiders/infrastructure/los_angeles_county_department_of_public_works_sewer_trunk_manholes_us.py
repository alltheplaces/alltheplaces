from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class LosAngelesCountyDepartmentOfPublicWorksSewerTrunkManholesUSSpider(ArcGISFeatureServerSpider):
    name = "los_angeles_county_department_of_public_works_sewer_trunk_manholes_us"
    item_attributes = {
        "operator": "Los Angeles County Department of Public Works",
        "operator_wikidata": "Q6682081",
        "state": "CA",
        "nsi_id": "N/A",
    }
    host = "dpw.gis.lacounty.gov"
    context_path = "dpw"
    service_id = "Sanitary_Sewer_Network"
    layer_id = "2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        apply_category(Categories.MANHOLE, item)
        item["extras"]["manhole"] = "sewer"
        yield item
