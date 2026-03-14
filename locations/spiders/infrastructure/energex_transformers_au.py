from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class EnergexTransformersAUSpider(ArcGISFeatureServerSpider):
    name = "energex_transformers_au"
    item_attributes = {"operator": "Energex", "operator_wikidata": "Q5376841"}
    host = "services.arcgis.com"
    context_path = "bfVzktoY0OhzQCDj/ArcGIS"
    service_id = "Network_Energex"
    layer_id = "1"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["USER_REF_I"]
        item["state"] = "QLD"
        apply_category(Categories.TRANSFORMER, item)
        if kva_rating := feature.get("MAX_KVA"):
            item["extras"]["rating"] = f"{kva_rating} kVA"
        if voltage_rating_str := feature.get("MAX_VOLT"):
            voltage_rating_int = int(voltage_rating_str) * 1000
            item["extras"]["voltage:primary"] = f"{voltage_rating_int}"
        yield item
