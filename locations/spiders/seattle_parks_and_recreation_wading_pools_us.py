from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationWadingPoolsUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_wading_pools_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Wading_Pools"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("OPENCLOSED", "").strip().lower() == "closed":
            return
        item["ref"] = str(feature["PMAID"])
        apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
        apply_yes_no(Extras.SWIMMING_POOL, item, "wading")
        yield item
