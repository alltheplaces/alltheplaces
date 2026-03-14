from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BrisbaneCityCouncilTrafficSignalsAUSpider(ArcGISFeatureServerSpider):
    name = "brisbane_city_council_traffic_signals_au"
    item_attributes = {"operator": "Brisbane City Council", "operator_wikidata": "Q56477660", "state": "QLD"}
    host = "services2.arcgis.com"
    context_path = "dEKgZETqwmDAh1rP/ArcGIS"
    service_id = "Traffic_Management_Signal_locations"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["TSC"])
        apply_category(Categories.HIGHWAY_TRAFFIC_SIGNALS, item)
        yield item
