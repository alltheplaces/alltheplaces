from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class RanchoCucamongaCityCouncilStreetLampsUSSpider(ArcGISFeatureServerSpider):
    name = "rancho_cucamonga_city_council_street_lamps_us"
    item_attributes = {
        "operator": "Rancho Cucamonga City Council",
        "operator_wikidata": "Q134606990",
        "state": "CA",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "bF44QtfoYZDGo7TK/arcgis"
    service_id = "StreetLights"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("GlobalID")
        item["street_address"] = feature.get("Location_D")
        apply_category(Categories.STREET_LAMP, item)

        if alt_ref := feature.get("RCID"):
            item["extras"]["alt_ref"] = alt_ref

        if ownership := feature.get("Ownership"):
            if ownership == "Private":
                item["operator"] = None
                item["operator_wikidata"] = None

        if height_ft := feature.get("Field_Height"):
            item["extras"]["height"] = f"{height_ft}'"

        if material := feature.get("Field_Material"):
            match material.strip():
                case "Concrete" | "Decorative Concrete":
                    item["extras"]["material"] = "concrete"
                case "NERI PPA" | "NERI RPA":
                    item["extras"]["material"] = "expoxy"
                case "Steel":
                    item["extras"]["material"] = "steel"
                case "Wood":
                    item["extras"]["material"] = "wood"
                case "Missing Pole" | "":
                    pass
                case _:
                    self.logger.warning("Unknown lamp pole material: {}".format(feature["Field_Material"]))

        yield item
