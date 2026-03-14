from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NswAmbulanceAUSpider(ArcGISFeatureServerSpider):
    name = "nsw_ambulance_au"
    item_attributes = {"operator": "NSW Ambulance", "operator_wikidata": "Q4741948"}
    host = "portal.spatial.nsw.gov.au"
    context_path = "server"
    service_id = "NSW_FOI_Health_Facilities"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["objectid"])
        item["name"] = feature["generalname"]
        item["state"] = "NSW"
        if " HEADQUARTERS" in item["name"]:
            apply_category({"office": "government"}, item)
            apply_category({"government": "emergency"}, item)
        elif " HELO AMBULANCE STATION" in item["name"]:
            apply_category({"emergency": "air_rescue_service"}, item)
        elif " CFR" in item["name"] or " VAO" in item["name"]:
            # Community First Responder (CFR) and Volunteer Ambulance Officer (VAO)
            apply_category({"emergency": "first_aid"}, item)
        else:
            apply_category({"emergency": "ambulance_station"}, item)
        if item["name"] in [
            "DICKSON AMBULANCE STATION",
            "GUNGAHLIN AMBULANCE STATION",
            "CALWELL AMBULANCE STATION",
            "PHILLIP AMBULANCE STATION",
            "KAMBAH AMBULANCE STATION",
            "WEST BELCONNEN AMBULANCE STATION",
            "BELCONNEN AMBULANCE STATION",
            "FYSHWICK AMBULANCE STATION",
            "GREENWAY AMBULANCE STATION",
            "SOUTHCARE HELO AMBULANCE STATION",
        ]:
            item["state"] = "ACT"
            item["operator"] = "Australian Capital Territory Ambulance Service"
            item["operator_wikidata"] = "Q4823922"
        yield item
