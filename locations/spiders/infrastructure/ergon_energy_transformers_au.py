from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class ErgonEnergyTransformersAUSpider(ArcGISFeatureServerSpider):
    name = "ergon_energy_transformers_au"
    item_attributes = {"operator": "Ergon Energy", "operator_wikidata": "Q5385825"}
    host = "services.arcgis.com"
    context_path = "33eHbTVqo7gtiCE8/ArcGIS"
    service_id = "Network_Extract"
    layer_id = "3"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["OP_NO"]
        item["name"] = feature.get("OP_DESC", feature.get("OP_NAME"))
        item["state"] = "QLD"
        apply_category(Categories.TRANSFORMER, item)
        if capacity_rating_str := feature.get("KVA"):
            capacity_rating_int = None
            if capacity_rating_str.endswith("kVA"):
                capacity_rating_int = int(capacity_rating_str.removesuffix("kVA").strip())
            elif capacity_rating_str:
                self.logger.warning("Cannot parse transformer capacity rating from: {}".format(capacity_rating_str))
            if capacity_rating_int:
                item["extras"]["rating"] = f"{capacity_rating_int} kVA"
        if voltage_rating_str := feature.get("PRIM_VOLT"):
            voltage_rating_int = None
            if voltage_rating_str.endswith(" kV"):
                voltage_rating_int = int(float(voltage_rating_str.removesuffix("kV").strip()) * 1000)
            elif voltage_rating_str.endswith(" V"):
                voltage_rating_int = int(float(voltage_rating_str.removesuffix("V").strip()))
            elif voltage_rating_str:
                self.logger.warning("Cannot parse transformer voltage rating from: {}".format(voltage_rating_str))
            if voltage_rating_int:
                item["extras"]["voltage:primary"] = f"{voltage_rating_int}"
        yield item
