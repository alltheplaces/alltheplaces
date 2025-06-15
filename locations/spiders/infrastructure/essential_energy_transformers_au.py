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
        item.pop("state", None)
        apply_category(Categories.TRANSFORMER, item)
        item["extras"]["alt_ref"] = feature["SW_LABEL"]
        if rating_kva := feature.get("KVA"):
            item["extras"]["rating"] = f"{rating_kva} kVA"
        if voltage_primary := feature.get("PRIMARY_VO"):
            item["extras"]["voltage:primary"] = voltage_primary.replace("kV", " kV")
        yield item
