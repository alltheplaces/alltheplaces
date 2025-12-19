from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationBaseballFieldsUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_baseball_fields_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Baseball_Softball_Fields"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["OBJECTID"])
        if courts := feature.get("BASEBALL"):
            if courts > 1:
                apply_category(Categories.LEISURE_SPORTS_CENTRE, item)
            else:
                apply_category(Categories.LEISURE_PITCH, item)
        apply_category({"sport": "baseball;softball"}, item)
        if lit := feature.get("E_LIGHTS"):
            if lit == "Yes":
                item["extras"]["lit"] = "yes"
            elif lit == "No":
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
