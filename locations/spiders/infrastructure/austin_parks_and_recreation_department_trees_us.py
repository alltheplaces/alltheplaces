from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AustinParksAndRecreationDepartmentTreesUSSpider(ArcGISFeatureServerSpider):
    name = "austin_parks_and_recreation_department_trees_us"
    item_attributes = {
        "operator": "Austin Parks and Recreation Department",
        "operator_wikidata": "Q115220147",
        "state": "TX",
    }
    host = "services.arcgis.com"
    context_path = "0L95CJ0VTaxqcmED/ArcGIS"
    service_id = "Public_PARD_Tree_Inventory_View"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item["ref"] = str(feature["GlobalID"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["species"] = feature["SCIENTIFIC_NAME"]
        item["extras"]["taxon:en"] = feature["SPECIES_NAME"]
        if dbh_in := feature.get("DBH"):
            item["extras"]["diameter"] = f"{dbh_in} in"
        yield item
