from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NswRuralFireServiceAUSpider(ArcGISFeatureServerSpider):
    name = "nsw_rural_fire_service_au"
    item_attributes = {"operator": "NSW Rural Fire Service", "operator_wikidata": "Q7011777"}
    host = "portal.spatial.nsw.gov.au"
    context_path = "server"
    service_id = "NSW_FOI_Emergency_Service_Facilities"
    layer_id = "2"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["objectid"])
        item["name"] = feature["generalname"]
        item["state"] = "NSW"
        if "ACT RFS " in item["name"]:
            item["state"] = "ACT"
        if (
            " RFB" in item["name"]
            or " FIRE CONTROL CENTRE" in item["name"]
            or "ACT RFS " in item["name"]
        ):
            apply_category(Categories.FIRE_STATION, item)
        else:
            apply_category({"office": "government", "government": "fire_service"}, item)
        yield item
