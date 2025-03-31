from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationPlaygroundsUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_playgrounds_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Play_Area"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("AMWO_ID")
        item["name"] = feature["PROPNAME"]
        apply_category(Categories.LEISURE_PLAYGROUND, item)
        yield item
