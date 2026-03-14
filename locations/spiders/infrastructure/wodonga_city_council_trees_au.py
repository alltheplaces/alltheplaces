import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class WodongaCityCouncilTreesAUSpider(ArcGISFeatureServerSpider):
    name = "wodonga_city_council_trees_au"
    item_attributes = {"operator": "Wodonga City Council", "operator_wikidata": "Q125664408"}
    host = "services-ap1.arcgis.com"
    context_path = "w6r4LlwgJu8O0neQ/ArcGIS"
    service_id = "Street_and_reserve_trees"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["assetid"]
        if addr_full := feature.get("fulladdr"):
            item["addr_full"] = re.sub(r"\s+", " ", addr_full).strip()
        apply_category(Categories.NATURAL_TREE, item)
        if taxon_en := feature.get("commonname"):
            item["extras"]["taxon:en"] = re.sub(r"\s+", " ", taxon_en).strip()
        if genus := feature.get("genus"):
            item["extras"]["genus"] = re.sub(r"\s+", " ", genus).strip()
        if species := feature.get("species"):
            item["extras"]["species"] = re.sub(r"\s+", " ", species).strip()
        if height := feature.get("height"):
            item["extras"]["height"] = str(round(float(height), 1))
        if dbh_cm := feature.get("diameter"):
            item["extras"]["diameter"] = f"{dbh_cm} cm"
        item["extras"]["protected"] = "yes"
        yield item
