from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class EssentialEnergyStreetLampsAUSpider(ArcGISFeatureServerSpider):
    name = "essential_energy_street_lamps_au"
    item_attributes = {"operator": "Essential Energy", "operator_wikidata": "Q17003842"}
    host = "services-ap1.arcgis.com"
    context_path = "3o0vFs4fJRsuYuBO/ArcGIS"
    service_id = "streetlight__STLT_"
    layer_id = "40"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["WACS_ID_A"]
        item["addr_full"] = feature["VICINITY"]
        apply_category(Categories.STREET_LAMP, item)
        item["extras"]["alt_ref"] = feature["W_LABEL_A"]
        if model := feature["PL_CAT_TAB"]:
            item["extras"]["model"] = model
        yield item
