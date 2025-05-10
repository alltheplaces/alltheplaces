from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class MassachusettsDepartmentOfTransportationManholesUSSpider(ArcGISFeatureServerSpider):
    name = "massachusetts_department_of_transportation_manholes_us"
    item_attributes = {
        "operator": "Massachusetts Department of Transportation",
        "operator_wikidata": "Q2483364",
        "state": "MA",
        "nsi_id": "N/A",
    }
    host = "gis.massdot.state.ma.us"
    context_path = "arcgis"
    service_id = "Assets/Stormwater"
    layer_id = "3"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["AssetID"]
        item["street"] = feature["St_Name"]
        item.pop("city", None)
        apply_category(Categories.MANHOLE, item)
        match feature["ManholeType"]:
            case "Large Round" | "Standard Round":
                item["extras"]["shape"] = "circular"
            case "Other" | None:
                pass
            case "Pullbox" | "Special Rectangular":
                item["extras"]["shape"] = "rectangular"
            case "Special Square":
                item["extras"]["shape"] = "square"
            case _:
                self.logger.warning("Unknown manhole shape: {}".format(feature["ManholeType"]))
        match feature["Utility"]:
            case "Combined sewer":
                item["extras"]["utility"] = "sewerage"
                item["extras"]["substance"] = "sewage;wastewater"
            case "Cable" | "Communication":
                item["extras"]["utility"] = "telecom"
            case "Drainage":
                item["extras"]["utility"] = "stormwater"
                item["extras"]["substance"] = "wastewater"
            case "Electric":
                item["extras"]["utility"] = "power"
            case "Gas":
                item["extras"]["utility"] = "gas"
                item["extras"]["substance"] = "gas"
            case "Sewer":
                item["extras"]["utility"] = "sewerage"
                item["extras"]["substance"] = "sewage"
            case "Unknown" | None:
                pass
            case "Water":
                item["extras"]["utility"] = "water"
                item["extras"]["substance"] = "water"
            case _:
                self.logger.warning("Unknown utility type: {}".format(feature["Utility"]))
        yield item
