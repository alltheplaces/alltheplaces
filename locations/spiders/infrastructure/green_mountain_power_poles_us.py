from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class GreenMountainPowerPolesUSSpider(ArcGISFeatureServerSpider):
    name = "green_mountain_power_poles_us"
    item_attributes = {"state": "VT", "nsi_id": "N/A"}
    host = "services1.arcgis.com"
    context_path = "BkFxaEFNwHqX3tAw/ArcGIS"
    service_id = "FS_VCGI_OPENDATA_Utility_GMP_Poles_point_SP_v1"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["POLETAG"]
        match feature["MAINTENANC"]:
            case "GMP":
                item["operator"] = "Green Mountain Power"
                item["operator_wikidata"] = "Q71871622"
            case "NGRD":
                item["operator"] = "National Grid USA"
                item["operator_wikidata"] = "Q1967266"
            case "TRANSMISSION" | "NONE":
                # "TRANSMISSION" and "NONE" seemingly are unknown/unspecified.
                pass
            case _:
                # Unknown maintainers: CHA, VMT, FNH.
                # "Fairpoint" appears to be a telecommunications company.
                self.logger.warning("Unknown power pole maintainer: {}".format(feature["MAINTENANC"]))
        apply_category(Categories.POWER_POLE, item)
        if height_ft := feature.get("POLEHEIGHT"):
            item["extras"]["height"] = f"{height_ft}'"
        yield item
