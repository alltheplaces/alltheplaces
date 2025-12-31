from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class LauncestonCityCouncilSewerAssetsAUSpider(ArcGISFeatureServerSpider):
    name = "launceston_city_council_sewer_assets_au"
    item_attributes = {"operator": "Launceston City Council", "operator_wikidata": "Q132860984", "state": "TAS"}
    host = "services.arcgis.com"
    context_path = "yeXpdyjk3azbqItW/ArcGIS"
    service_id = "Utilities"
    layer_id = "4"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if asset_id := feature.get("Assetid"):
            item["ref"] = str(asset_id)
        else:
            item["ref"] = feature.get("Globalid")

        if asset_type := feature.get("Type"):
            match asset_type:
                case "Sewer Manhole" | "Inspection Opening":
                    apply_category(Categories.MANHOLE, item)
                    item["extras"]["manhole"] = "sewer"
                    item["extras"]["utility"] = "sewerage"
                    item["extras"]["substance"] = "sewage"
                case "Pump Station":
                    apply_category(Categories.PUMPING_STATION_SEWAGE, item)
                case "Vent":
                    apply_category(Categories.SEWER_VENT, item)
                case "Waste Water Treatment Plant":
                    apply_category(Categories.WASTEWATER_PLANT, item)
                case (
                    "Abandoned Pump Station"
                    | "Air Valve"
                    | "Dump Point"
                    | "End of Line"
                    | "Estimated Sewer Manhole"
                    | "Flow Meter"
                    | "Grease Trap"
                    | "Junction"
                    | "No Type Allocated"
                    | "Stop Valve"
                ):
                    return
                case _:
                    self.logger.warning("Unknown sewer feature type: {}".format(feature["Type"]))
                    return

            yield item
