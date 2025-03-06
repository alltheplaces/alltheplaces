from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CambridgeCityCouncilFireHydrantsUSSpider(ArcGISFeatureServerSpider):
    name = "cambridge_city_council_fire_hydrants_us"
    item_attributes = {"operator": "Cambridge City Council", "operator_wikidata": "Q133054988", "state": "MA"}
    host = "services1.arcgis.com"
    context_path = "WnzC35krSYGuYov4/ArcGIS"
    service_id = "Hydrants"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if hydrant_id := feature.get("HYDRANT_ID"):
            item["ref"] = str(hydrant_id)
        else:
            item["ref"] = feature["GlobalID"]
        apply_category(Categories.FIRE_HYDRANT, item)
        if flow_rate_gpm := feature.get("HYDRANT_GPM"):
            item["extras"]["flow_rate"] = f"{flow_rate_gpm} usgal/min"
        yield item
