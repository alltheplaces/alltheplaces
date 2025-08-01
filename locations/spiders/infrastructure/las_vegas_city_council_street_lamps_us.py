from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class LasVegasCityCouncilStreetLampsUSSpider(ArcGISFeatureServerSpider):
    name = "las_vegas_city_council_street_lamps_us"
    item_attributes = {
        "operator": "Las Vegas City Council",
        "operator_wikidata": "Q105801990",
        "state": "NV",
        "nsi_id": "N/A",
    }
    host = "services1.arcgis.com"
    context_path = "F1v0ufATbBQScMtY/ArcGIS"
    service_id = "stlights"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["UNITID"])
        apply_category(Categories.STREET_LAMP, item)
        match feature["MATERIAL"]:
            case "CONCRT":
                item["extras"]["material"] = "concrete"
            case "STEEL":
                item["extras"]["material"] = "steel"
            case "WOOD":
                item["extras"]["material"] = "wood"
            case "DAVIT" | "DCRTV" | None:
                pass
            case _:
                self.logger.warning("Unknown material type: {}".format(feature["POLE_TYPE"]))
        if height_ft := feature["MASTLENGTH"]:
            item["extras"]["height"] = f"{height_ft}'"
        yield item
