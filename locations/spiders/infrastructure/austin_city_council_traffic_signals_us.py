from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AustinCityCouncilTrafficSignalsUSSpider(ArcGISFeatureServerSpider):
    name = "austin_city_council_traffic_signals_us"
    item_attributes = {"operator": "Austin City Council", "operator_wikidata": "Q85744182", "state": "TX"}
    host = "services.arcgis.com"
    context_path = "0L95CJ0VTaxqcmED/ArcGIS"
    service_id = "TRANSPORTATION_signals2"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("SIGNAL_STATUS") != "TURNED_ON":
            return
        item["ref"] = str(feature["SIGNAL_ID"])
        apply_category(Categories.HIGHWAY_TRAFFIC_SIGNALS, item)
        yield item
