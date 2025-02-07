import re
from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HobsonsBayCityCouncilTreesAUSpider(ArcGISFeatureServerSpider):
    name = "hobsons_bay_city_council_trees_au"
    item_attributes = {"operator": "Hobsons Bay City Council", "operator_wikidata": "Q56477824"}
    host = "services3.arcgis.com"
    context_path = "gToGKwidNkZbWBGJ/ArcGIS"
    service_id = "Trees_point"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["Central_As"]
        item["addr_full"] = re.sub(r"\s+", " ", feature["Feature_Lo"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["taxon:en"] = feature["T_Common_N"]
        item["extras"]["genus"] = feature["T_Genus"]
        item["extras"]["species"] = feature["T_Species"]
        item["extras"]["height"] = feature["T_Tree_Hei"]
        item["extras"]["protected"] = "yes"
        yield item
