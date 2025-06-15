from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class LosAngelesCountyDepartmentOfPublicWorksTreesUSSpider(ArcGISFeatureServerSpider):
    name = "los_angeles_county_department_of_public_works_trees_us"
    item_attributes = {
        "operator": "Los Angeles County Department of Public Works",
        "operator_wikidata": "Q6682081",
        "state": "CA",
        "nsi_id": "N/A",
    }
    host = "dpw.gis.lacounty.gov"
    context_path = "dpw"
    service_id = "GIS_Web_Services"
    server_type = "MapServer"
    layer_id = "3"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["ASSET_ID"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["taxon:en"] = feature["SPECIES"]
        if height_ft := feature.get("HEIGHT"):
            item["extras"]["height"] = f"{height_ft} '"
        if dbh_in := feature.get("DIAMETER"):
            item["extras"]["diameter"] = f"{dbh_in} in"
        if dcrown_ft := feature.get("SPREAD"):
            item["extras"]["diameter_crown"] = f"{dcrown_ft} '"
        yield item
