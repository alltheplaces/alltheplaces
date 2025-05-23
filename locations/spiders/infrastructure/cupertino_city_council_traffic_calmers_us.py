from typing import Iterable

from scrapy.http import Response

from locations.categories import apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CupertinoCityCouncilTrafficCalmersUSSpider(ArcGISFeatureServerSpider):
    name = "cupertino_city_council_traffic_calmers_us"
    item_attributes = {
        "operator": "Cupertino City Council",
        "operator_wikidata": "Q134548005",
        "state": "CA",
        "nsi_id": "N/A",
    }
    host = "gis.cupertino.org"
    context_path = "cupgis"
    service_id = "Public/AmazonData"
    layer_id = "32"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("AssetID")
        match feature["DeviceType"]:
            case "Bollard":
                apply_category({"barrier": "bollard"}, item)
            case "Chatter Bar":
                apply_category({"traffic_calming": "rumble_strip"}, item)
            case "Choker":
                apply_category({"traffic_calming": "choker"}, item)
            case "Delineator" | "Raised Curb W Delineator":
                apply_category({"barrier": "delineators"}, item)
                if delineator_height_in := feature.get("DelineatorHeight"):
                    item["extras"]["height"] = f'{delineator_height_in}"'
            case "OM2-2H":
                # Reflective sign -- ignore.
                return
            case "Raised Curb":
                # Unknown calming device -- ignore.
                return
            case "Soldier":
                # Unknown calming device -- ignore.
                return
            case "Speed Bump":
                apply_category({"traffic_calming": "bump"}, item)
            case "Speed Hump":
                apply_category({"traffic_calming": "hump"}, item)
            case "Speed Table":
                apply_category({"traffic_calming": "table"}, item)
            case "Type Q":
                # Unknown calming device -- ignore.
                return
            case _:
                self.logger.warning("Unknown traffic calming device type: {}".format(feature["DeviceType"]))
                return
        yield item
