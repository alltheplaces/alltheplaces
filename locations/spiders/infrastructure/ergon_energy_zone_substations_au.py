import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class ErgonEnergyZoneSubstationsAUSpider(ArcGISFeatureServerSpider):
    name = "ergon_energy_zone_substations_au"
    item_attributes = {"operator": "Ergon Energy", "operator_wikidata": "Q5385825"}
    host = "services.arcgis.com"
    context_path = "33eHbTVqo7gtiCE8/ArcGIS"
    service_id = "Network_Extract"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["OP_NO"]
        item["name"] = feature.get("OP_DESC", feature.get("OP_NAME"))
        voltages_from_name = set()
        if item["name"]:
            voltages_from_name = set(
                map(
                    lambda x: int(float(x) * 1000),
                    re.findall(r"(\d+(?:\.\d+)?)(?=(?:\/|KV))", item["name"], flags=re.IGNORECASE),
                )
            )
        if voltage_rating_str := feature.get("OP_VOLT"):
            voltage_rating_int = None
            if voltage_rating_str.endswith(" kV"):
                voltage_rating_int = int(float(voltage_rating_str.removesuffix("kV").strip()) * 1000)
            elif voltage_rating_str.endswith(" V"):
                voltage_rating_int = int(float(voltage_rating_str.removesuffix("V").strip()))
            elif voltage_rating_str:
                self.logger.warning(
                    "Cannot parse substation maximum voltage rating from: {}".format(voltage_rating_str)
                )
            if voltage_rating_int:
                voltages_from_name.add(voltage_rating_int)
        voltages = list(map(lambda x: str(x), sorted(list(voltages_from_name), reverse=True)))
        item["extras"]["voltage"] = ";".join(voltages)
        item["state"] = "QLD"
        if item["name"] and ("BULK SUPPLY" in item["name"].upper() or "SWITCHING STATION" in item["name"].upper()):
            apply_category(Categories.SUBSTATION_TRANSMISSION, item)
        else:
            apply_category(Categories.SUBSTATION_ZONE, item)
        yield item
