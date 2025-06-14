from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class NiagaraFallsCityCouncilStreetLampsCASpider(ArcGISFeatureServerSpider):
    name = "niagara_falls_city_council_street_lamps_ca"
    item_attributes = {"state": "ON", "nsi_id": "N/A"}
    host = "services9.arcgis.com"
    context_path = "oMFQlUUrLd1Uh1bd/ArcGIS"
    service_id = "Niagara_Falls_Street_Light_Supports"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature["Status"].upper() != "ACTIVE":
            return
        item["ref"] = feature["ID"]
        match feature["Custodian"]:
            case "CITY OF NIAGARA FALLS":
                item["operator"] = "Niagara Falls City Council"
                item["operator_wikidata"] = "Q16941501"
            case "HYDRO ONE NETWORK INC":
                item["operator"] = "Hydro One"
                item["operator_wikidata"] = "Q3143709"
            case "MINISTRY OF TRANSPORTATION":
                item["operator"] = "Ministry of Transportation"
                item["operator_wikidata"] = "Q3315416"
            case "NIAGARA PENINSULA ENERGY INCORPORATED":
                item["operator"] = "Niagara Peninsula Energy Incorporated"
                item["operator_wikidata"] = "Q133141596"
            case "REGIONAL MUNICIPALITY OF NIAGARA":
                item["operator"] = "Regional Municipality of Niagara Council"
                item["operator_wikidata"] = "Q133143023"
            case None:
                pass
            case _:
                self.logger.warning("Unknown operator: {}".format(feature["Custodian"]))
        apply_category(Categories.STREET_LAMP, item)
        item["extras"]["alt_ref"] = feature["Field_ID"]
        if height_m := feature["PoleHeight"]:
            item["extras"]["height"] = f"{height_m}"
        if material := feature.get("Material"):
            match material.upper():
                case "ALUMINIUM":
                    item["extras"]["material"] = "aluminium"
                case "CONCRETE" | "EXPOSED AGGREGATE BLACK":
                    item["extras"]["material"] = "concrete"
                case "FIBERGLASS":
                    item["extras"]["material"] = "fiberglass"
                case "STEEL":
                    item["extras"]["material"] = "steel"
                case "WOOD":
                    item["extras"]["material"] = "wood"
                case "UNKNOWN" | "OTHER" | None:
                    pass
                case _:
                    self.logger.warning("Unknown lamp pole material: {}".format(feature["Material"]))
        yield item
