from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class WesternPowerStreetLampsAUSpider(ArcGISFeatureServerSpider):
    name = "western_power_street_lamps_au"
    item_attributes = {"operator": "Western Power", "operator_wikidata": "Q7988180"}
    host = "services2.arcgis.com"
    context_path = "tBLxde4cxSlNUxsM/ArcGIS"
    service_id = "Streetlight_Prod"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["PICK_ID"]
        item["street_address"] = item.pop("addr_full")
        item["state"] = "WA"
        apply_category(Categories.STREET_LAMP, item)
        item["extras"]["alt_ref"] = feature["POLE_PID"]
        yield item
