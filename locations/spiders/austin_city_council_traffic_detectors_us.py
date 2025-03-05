from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AustinCityCouncilTrafficDetectorsUSSpider(ArcGISFeatureServerSpider):
    name = "austin_city_council_traffic_detectors_us"
    item_attributes = {"operator": "Austin City Council", "operator_wikidata": "Q85744182"}
    host = "services.arcgis.com"
    context_path = "0L95CJ0VTaxqcmED/ArcGIS"
    service_id = "traffic_detectors"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("DETECTOR_STATUS") != "OK":
            return
        item["ref"] = str(feature["DETECTOR_ID"])
        apply_category(Categories.MONITORING_STATION, item)
        apply_yes_no(MonitoringTypes.TRAFFIC, item, True)
        yield item
