from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class AustinCityCouncilTrafficCamerasUSSpider(ArcGISFeatureServerSpider):
    name = "austin_city_council_traffic_cameras_us"
    item_attributes = {"operator": "Austin City Council", "operator_wikidata": "Q85744182"}
    host = "services.arcgis.com"
    context_path = "0L95CJ0VTaxqcmED/ArcGIS"
    service_id = "TRANSPORTATION_traffic_cameras"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("CAMERA_STATUS") != "TURNED_ON":
            return
        item["ref"] = str(feature["CAMERA_ID"])
        item["addr_full"] = feature["location"]
        apply_category(Categories.SURVEILLANCE_CAMERA, item)
        item["extras"]["contact:webcam"] = feature["SCREENSHOT_ADDRESS"]
        match feature["SIGNAL_ENG_AREA"]:
            case "NORTH":
                item["extras"]["camera:direction"] = "N"
            case "NORTHEAST":
                item["extras"]["camera:direction"] = "NE"
            case "EAST":
                item["extras"]["camera:direction"] = "E"
            case "SOUTHEAST":
                item["extras"]["camera:direction"] = "SE"
            case "SOUTH":
                item["extras"]["camera:direction"] = "S"
            case "SOUTHWEST":
                item["extras"]["camera:direction"] = "SW"
            case "WEST":
                item["extras"]["camera:direction"] = "W"
            case "NORTHWEST":
                item["extras"]["camera:direction"] = "NW"
            case "CENTRAL" | None:
                pass
            case _:
                self.logger.warning("Unknown camera direction: {}".format(feature["SIGNAL_ENG_AREA"]))
        yield item
