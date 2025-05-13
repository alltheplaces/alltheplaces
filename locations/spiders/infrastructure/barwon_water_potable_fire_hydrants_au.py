from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class BarwonWaterPotableFireHydrantsAUSpider(ArcGISFeatureServerSpider):
    name = "barwon_water_potable_fire_hydrants_au"
    item_attributes = {"operator": "Barwon Water", "operator_wikidata": "Q4865988"}
    host = "services8.arcgis.com"
    context_path = "uLK1YQYKdEhgFHsx/ArcGIS"
    service_id = "Barwon_Water_Fire_Services"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = str(feature["BW_ASSET_ID"])
        apply_category(Categories.FIRE_HYDRANT, item)
        item["extras"]["substance"] = "water"

        if hydrant_type := feature.get("NODE_TYPE"):
            match hydrant_type:
                case "FP":  # Fire plug
                    item["extras"]["fire_hydrant:type"] = "underground"
                case "PH":  # Pillar hydrant
                    item["extras"]["fire_hydrant:type"] = "pillar"
                case _:
                    self.logger.warning("Unknown fire hydrant type: {}".format(hydrant_type))

        if depth_str := feature.get("NODE_DEPTH"):
            if depth_str != "UNK" and depth_str != "AG":  # AG = Above Ground
                try:
                    depth_float = round(float(depth_str), 1)
                    item["extras"]["depth"] = f"{depth_float} m"
                except ValueError:
                    pass

        if diameter_str := feature.get("NODE_DIA"):
            if diameter_str != "UNK":
                try:
                    diameter_int = int(diameter_str)
                    item["extras"]["fire_hydrant:diameter"] = f"{diameter_int} mm"
                except ValueError:
                    pass

        if pressure_str := feature.get("MAX_PRESSURE"):
            if pressure_str != "UNK":
                try:
                    pressure_float = round(float(pressure_str), 1)
                    item["extras"]["fire_hydrant:pressure"] = f"{pressure_float} mH2O"
                except ValueError:
                    pass

        if elevation_str := feature.get("NODE_ELEV"):
            if elevation_str != "UNK":
                try:
                    elevation_float = round(float(elevation_str), 1)
                    item["extras"]["ele"] = f"{elevation_float} m"
                except ValueError:
                    pass

        yield item
