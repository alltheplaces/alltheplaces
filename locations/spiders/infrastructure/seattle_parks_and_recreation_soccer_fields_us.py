from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationSoccerFieldsUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_soccer_fields_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Soccer_Fields"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "(Closed)" in feature.get("NAME"):
            return
        item["ref"] = str(feature.get("OBJECTID"))
        apply_category(Categories.LEISURE_PITCH, item)
        apply_category({"sport": "soccer"}, item)
        if lit := feature.get("E_LIGHTS"):
            if lit == "Yes":
                item["extras"]["lit"] = "yes"
            elif lit == "no":
                item["extras"]["lit"] = "no"
        match feature.get("E_SURFACE"):
            case "Grass":
                item["extras"]["surface"] = "grass"
            case "Synthetic":
                item["extras"]["surface"] = "artificial_turf"
            case "Synthetic and Grass" | "Synthetic, Grass":
                item["extras"]["surface"] = "artificial_turf;grass"
            case _:
                self.logger.warning("Unknown material type: {}".format(feature["E_SURFACE"]))
        yield item
