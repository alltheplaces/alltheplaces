from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SaPowerNetworksZoneSubstationsAUSpider(ArcGISFeatureServerSpider):
    name = "sa_power_networks_zone_substations_au"
    item_attributes = {"operator": "SA Power Networks", "operator_wikidata": "Q7388891"}
    host = "pirsa.geohub.sa.gov.au"
    context_path = "server"
    service_id = "AgInsight_Services/SIS_AgInsight_Electricity_P"
    server_type = "MapServer"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        item["state"] = "SA"
        apply_category(Categories.SUBSTATION_ZONE, item)
        yield item
