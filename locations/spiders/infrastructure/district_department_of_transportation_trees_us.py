from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class DistrictDepartmentOfTransportationTreesUSSpider(ArcGISFeatureServerSpider):
    name = "district_department_of_transportation_trees_us"
    item_attributes = {"operator": "District Department of Transportation", "operator_wikidata": "Q4923837", "state": "DC"}
    host = "maps2.dcgis.dc.gov"
    context_path = "dcgis"
    service_id = "DDOT/UFATrees2"
    server_type = "MapServer"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["FACILITYID"]
        if street_address := feature.get("VICINITY"):
            item["street_address"] = street_address
        apply_category(Categories.NATURAL_TREE, item)
        if species := feature.get("SCI_NM"):
            item["extras"]["species"] = species
        if genus := feature.get("GENUS_NAME"):
            item["extras"]["genus"] = genus
        if common_name := feature.get("CMMN_NM"):
            item["extras"]["taxon:en"] = common_name
        if dbh_in := feature.get("DBH"):
            item["extras"]["diameter"] = f"{dbh_in}\""
        yield item

