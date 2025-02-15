from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class ElectranetTransmissionSubstationsAUSpider(ArcGISFeatureServerSpider):
    name = "electranet_transmission_substations_au"
    item_attributes = {"operator": "ElectraNet", "operator_wikidata": "Q5357218"}
    host = "pirsa.geohub.sa.gov.au"
    context_path = "server"
    service_id = "AgInsight_Services/SIS_AgInsight_Electricity_P"
    server_type = "MapServer"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        item["state"] = "SA"
        apply_category(Categories.SUBSTATION_TRANSMISSION, item)
        if voltage_rating_int := feature.get("VOLTAGE_KV"):
            item["extras"]["voltage"] = str(voltage_rating_int * 1000)
        yield item
