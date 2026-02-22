from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class HastingsDistrictCouncilTreesNZSpider(ArcGISFeatureServerSpider):
    name = "hastings_district_council_trees_nz"
    item_attributes = {"operator": "Hastings District Council", "operator_wikidata": "Q73811101"}
    host = "services1.arcgis.com"
    context_path = "8L3DQUzjrkgEmDpQ/ArcGIS"
    service_id = "Hastings_DC_Trees"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["protected"] = "yes"
        item["extras"]["species"] = feature["tree_species"]
        item["extras"]["taxon:en"] = feature["common_name"]
        yield item
