from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AlbanyCityCouncilTreesAUSpider(ArcGISFeatureServerSpider):
    name = "albany_city_council_trees_au"
    item_attributes = {"operator": "Albany City Council", "operator_wikidata": "Q132397580", "state": "WA"}
    host = "services6.arcgis.com"
    context_path = "qG6LEFhXeMyvh3U3/ArcGIS"
    service_id = "MANAGED_SPACE_V1_4_2024_view"
    layer_id = "15"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["tree_id"])
        apply_category(Categories.NATURAL_TREE, item)
        item["extras"]["taxon:en"] = feature["common_nam"]
        item["extras"]["species"] = feature["botan_nam"]
        item["extras"]["protected"] = "yes"
        yield item
