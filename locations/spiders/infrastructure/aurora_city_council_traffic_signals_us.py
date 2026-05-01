from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AuroraCityCouncilTrafficSignalsUSSpider(ArcGISFeatureServerSpider):
    name = "aurora_city_council_traffic_signals_us"
    item_attributes = {"operator": "Aurora City Council", "operator_wikidata": "Q138498688", "state": "CO"}
    host = "services3.arcgis.com"
    context_path = "0Va1ID99NSrNyyPX/arcgis"
    service_id = "Traffic_Signal_Infrastructure_Signalized_Intersections_View_Only"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("SIGNAL_TYPE") not in ("EXISTING", "REBUILT"):
            return
        item["ref"] = feature["GlobalID"]
        item["name"] = feature.get("INTERSECTION")
        apply_category(Categories.HIGHWAY_TRAFFIC_SIGNALS, item)
        if imaster_number := feature.get("IMASTER_NUMBER"):
            item["extras"]["alt_ref"] = str(imaster_number)
        yield item
