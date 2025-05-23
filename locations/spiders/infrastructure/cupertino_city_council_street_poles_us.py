from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class CupertinoCityCouncilStreetPolesUSSpider(ArcGISFeatureServerSpider):
    name = "cupertino_city_council_street_poles_us"
    item_attributes = {"operator": "Cupertino City Council", "operator_wikidata": "Q134548005", "state": "CA", "nsi_id": "N/A"}
    host = "gis.cupertino.org"
    context_path = "cupgis"
    service_id = "Public/AmazonData"
    layer_id = "40"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("AssetID")
        if feature.get("isStreetlight") == "Y":
            apply_category(Categories.STREET_LAMP, item)
        if feature.get("IsTrafficSignal") == "Y":
            apply_category(Categories.HIGHWAY_TRAFFIC_SIGNALS, item)
        pole_material = feature.get("PoleMaterial")
        if pole_material:
            pole_material = pole_material.strip()
        match pole_material:
            case "Aluminium" | "ALUMINUM":
                item["extras"]["material"] = "aluminium"
            case "Concrete":
                item["extras"]["material"] = "concrete"
            case "Wood" | "STANDARD WOOD" | "CENTER BORE WOOD":
                item["extras"]["material"] = "wood"
            case "Steel" | "STEEL" | "Galvanized" | "GALVANIZED":
                item["extras"]["material"] = "steel"
            case "UNKNOWN" | "OTHER" | "" | None:
                pass
            case _:
                self.logger.warning("Unknown pole material: {}".format(pole_material))
        if pole_height_ft := feature.get("PoleHeight"):
            item["extras"]["height"] = f"{pole_height_ft}'"
        yield item
