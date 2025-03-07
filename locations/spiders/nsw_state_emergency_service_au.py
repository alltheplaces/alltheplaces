from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NswStateEmergencyServiceAUSpider(ArcGISFeatureServerSpider):
    name = "nsw_state_emergency_service_au"
    item_attributes = {"operator": "NSW State Emergency Service", "operator_wikidata": "Q7011790", "nsi_id": "N/A"}
    host = "portal.spatial.nsw.gov.au"
    context_path = "server"
    service_id = "NSW_FOI_Emergency_Service_Facilities"
    layer_id = "3"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["objectid"])
        item["name"] = feature["generalname"]
        item["state"] = "NSW"
        if item["name"][:4] == "ACT ":
            item["state"] = "ACT"
        if " HEADQUARTERS" in item["name"]:
            apply_category({"office": "government", "government": "emergency"}, item)
        elif "MARINE RESCUE " in item["name"]:
            apply_category({"emergency": "water_rescue"}, item)
        elif (
            " SES" in item["name"]
            or " MINES RESCUE STATION" in item["name"]
            or ("ACT ESA " in item["name"] and " UNIT" in item["name"])
        ):
            apply_category({"amenity": "rescue_station"}, item)
        else:
            apply_category({"office": "government", "government": "emergency"}, item)
        yield item
