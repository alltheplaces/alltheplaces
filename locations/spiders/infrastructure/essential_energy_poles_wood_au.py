from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class EssentialEnergyPolesWoodAUSpider(ArcGISFeatureServerSpider):
    name = "essential_energy_poles_wood_au"
    item_attributes = {"operator": "Essential Energy", "operator_wikidata": "Q17003842"}
    host = "services-ap1.arcgis.com"
    context_path = "3o0vFs4fJRsuYuBO/ArcGIS"
    service_id = "pole_timber_PTIM_"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["WACS_ID_A"])
        item.pop("state", None)
        apply_category(Categories.POWER_POLE, item)
        item["extras"]["alt_ref"] = feature["W_LABEL_A"]
        item["extras"]["material"] = "wood"
        if height_m := feature.get("LENGTH"):
            item["extras"]["height"] = f"{height_m} m"
        yield item
