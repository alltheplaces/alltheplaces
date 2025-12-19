from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class EssentialEnergyPolesMetalAUSpider(ArcGISFeatureServerSpider):
    name = "essential_energy_poles_metal_au"
    item_attributes = {"operator": "Essential Energy", "operator_wikidata": "Q17003842"}
    host = "services-ap1.arcgis.com"
    context_path = "3o0vFs4fJRsuYuBO/ArcGIS"
    service_id = "pole_metal__PMET_"
    layer_id = "4"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["WACS_ID_A"]
        item.pop("state", None)
        apply_category(Categories.POWER_POLE, item)
        item["extras"]["alt_ref"] = feature["W_LABEL_A"]
        item["extras"]["material"] = "metal"
        if height_m := feature.get("LENGTH_"):
            item["extras"]["height"] = f"{height_m} m"
        yield item
