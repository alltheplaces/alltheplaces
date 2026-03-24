from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class EvanstonCityCouncilTrafficSignalsUSSpider(ArcGISFeatureServerSpider):
    name = "evanston_city_council_traffic_signals_us"
    item_attributes = {"operator": "Evanston City Council", "operator_wikidata": "Q138498023", "state": "IL"}
    host = "maps.cityofevanston.org"
    context_path = "arcgis"
    service_id = "OpenData/ArcGISOpenData4Transportation"
    server_type = "MapServer"
    layer_id = "4"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["GlobalID"]
        item["name"] = feature.get("Label")
        apply_category(Categories.HIGHWAY_TRAFFIC_SIGNALS, item)
        yield item
