import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.settings import ITEM_PIPELINES
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class ErgonEnergyTransformersAUSpider(ArcGISFeatureServerSpider):
    name = "ergon_energy_transformers_au"
    item_attributes = {"operator": "Ergon Energy", "operator_wikidata": "Q5385825"}
    host = "services.arcgis.com"
    context_path = "33eHbTVqo7gtiCE8/ArcGIS"
    service_id = "Network_Extract"
    layer_id = "3"
    # Disable ClosePipeline because it gets stuck on names such as
    # "500kVA ENCLOSED TRANSFORMER" (contains "CLOSED").
    custom_settings = {"ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.closed.ClosePipeline": None}}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["OP_NO"]
        item["name"] = feature.get("OP_DESC", feature.get("OP_NAME"))
        item["state"] = "QLD"
        apply_category(Categories.TRANSFORMER, item)

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

        if capacity_rating_str := feature.get("KVA"):
            capacity_rating_int = None
            if m := re.match(r"^\s*(\d+(?:\.\d+)?)\s*kVA\s*$", capacity_rating_str):
                # Expressed as kVA rating
                capacity_rating_int = int(m.group(1).strip().removesuffix("kVA").strip())
            elif m := re.match(r"^\s*(\d+(?:\.\d+)?)\s*A\s*$", capacity_rating_str):
                # Also expressed as kVA rating, but with incorrect units of A.
                # A check of numerous of these capacities with units of A
                # confirms standard kVA ratings of 50, 100, 200kVA used and
                # pole mounted transformers used, thus units of A is not
                # implying high-voltage or low-voltage per-phase amperages.
                capacity_rating_int = int(m.group(1).strip().removesuffix("A").strip())
            elif m := re.match(r"^\s*(\d+(?:\.\d+)?)\s*MVA\s*$", capacity_rating_str):
                # Expressed as MVA rating
                capacity_rating_int = round(int(m.group(1).strip().removesuffix("MVA").strip()) * 1000, 2)
            elif capacity_rating_str in ["NA", "Unknown"]:
                pass
            elif capacity_rating_str:
                self.logger.warning("Cannot parse transformer capacity rating from: {}".format(capacity_rating_str))
            if capacity_rating_int:
                item["extras"]["rating"] = f"{capacity_rating_int} kVA"

        yield item
