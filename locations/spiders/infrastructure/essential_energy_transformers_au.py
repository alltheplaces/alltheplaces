from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class EssentialEnergyTransformersAUSpider(ArcGISFeatureServerSpider):
    name = "essential_energy_transformers_au"
    item_attributes = {"operator": "Essential Energy", "operator_wikidata": "Q17003842"}
    host = "services-ap1.arcgis.com"
    context_path = "3o0vFs4fJRsuYuBO/ArcGIS"
    service_id = "transformer__XFMR_"
    layer_id = "29"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["WACS_ID_A"]
        item["addr_full"] = feature["VICINITY"]
        apply_category(Categories.TRANSFORMER, item)
        item["extras"]["alt_ref"] = feature["W_LABEL_A"]
        if voltage_kv_str := feature["PRIMARY_VO"]:
            try:
                voltage_v = int(float(voltage_kv_str.strip().removesuffix("kV").strip()) * 1000)
                item["extras"]["voltage:primary"] = f"{voltage_v}"
            except ValueError:
                pass
        if rating := feature["KVA"]:
            item["extras"]["rating"] = rating + " kVA"
        yield item
