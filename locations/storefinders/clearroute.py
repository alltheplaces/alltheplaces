from copy import deepcopy
from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, MonitoringTypes, apply_category, apply_yes_no
from locations.items import Feature


class ClearRouteSpider(Spider):
    """
    Iteris ClearRoute is an Advanced Traveler Information System (ATIS) used
    for real time traffic monitoring and management. The following types of
    information are made available through public traffic information
    websites:
    - Webcam feeds for monitoring traffic congestion
    - Webcam feeds for Road Weather Information Systems (RWIS)
    - RWIS data feeds

    To use, specify:
     - 'customer_id': mandatory parameter, as found in URLs of:
                      https://{customer_id}.cdn.iteris-atis.com/...
     - 'features": optional parameter, set to something other than the default
                   of ["cameras", "rwis"] (example: ["cameras"]) to skip a
                   type of feature that it not available for the customer.
    """

    customer_id: str = ""
    features: list[str] = ["cameras", "rwis"]

    def start_requests(self) -> Iterable[JsonRequest]:
        if "cameras" in self.features:
            yield JsonRequest(url=f"https://{self.customer_id}.cdn.iteris-atis.com/geojson/icons/metadata/icons.cameras.geojson", callback=self.parse_cameras)
        if "rwis" in self.features:
            yield JsonRequest(url=f"https://{self.customer_id}.cdn.iteris-atis.com/geojson/icons/metadata/icons.rwis.geojson", callback=self.parse_rwis)

    def parse_cameras(self, response: Response) -> Iterable[Feature]:
        for camera in response.json()["features"]:
            if camera.get("active") is False:
                # Camera is disabled/not working and should be ignored.
                continue
            properties = {
                "ref": next(filter(None, [camera["properties"].get("id"), camera.get("id")])),
                "name": next(filter(None, [camera["properties"].get("description"), camera["properties"].get("name")])),
                "geometry": camera["geometry"],
            }
            apply_category(Categories.SURVEILLANCE_CAMERA, properties)
            if len(camera["properties"].get("cameras", [])) > 0:
                properties["extras"]["contact:webcam"] = ";".join([view["image"] for view in camera["properties"].get("cameras")])
                if len(camera["properties"]["cameras"]) > 1:
                    properties["extras"]["camera:type"] = "dome"
                else:
                    properties["extras"]["camera:type"] = "fixed"
            elif camera.get("rtmp_url") or camera.get("rtsp_url") or camera.get("https_url") or camera.get("image_url"):
                properties["extras"]["contact:webcam"] = ";".join(filter(None, [camera.get("rtmp_url"), camera.get("rtsp_url"), camera.get("https_url"), camera.get("image_url")]))
                properites["extras"]["camera:type"] = "fixed"
            yield Feature(**properties)

    def parse_rwis(self, response: Response) -> Iterable[Feature]:
        for rwis in response.json()["features"]:
            common_properties = {
                "ref": next(filter(None, [rwis["properties"].get("id"), rwis.get("id")])),
                "name": next(filter(None, [rwis["properties"].get("description"), rwis["properties"].get("name")])),
                "geometry": rwis["geometry"],
            }

            rwis_properties = deepcopy(common_properties)
            rwis_properties["ref"] = rwis_properties["ref"] + "_RWIS"
            apply_category(Categories.MONITORING_STATION, rwis_properties)
            if len(rwis["properties"].get("atmos", [])) > 0:
                apply_yes_no(MonitoringTypes.AIR_HUMIDITY, rwis_properties, "relative_humidity" in rwis["properties"]["atmos"][0].keys(), False)
                apply_yes_no(MonitoringTypes.AIR_TEMPERATURE, rwis_properties, "air_temperature" in rwis["properties"]["atmos"][0].keys() or "dewpoint_temperature" in rwis["properties"]["atmos"][0].keys(), False)
                apply_yes_no(MonitoringTypes.PRECIPITATION, rwis_properties, "precip_accumulated" in rwis["properties"]["atmos"][0].keys() or "precip_rate" in rwis["properties"]["atmos"][0].keys(), False)
                apply_yes_no(MonitoringTypes.WIND_DIRECTION, rwis_properties, "wind_direction" in rwis["properties"]["atmos"][0].keys(), False)
                apply_yes_no(MonitoringTypes.WIND_SPEED, rwis_properties, "wind_speed" in rwis["properties"]["atmos"][0].keys(), False)
            yield Feature(**rwis_properties)

            if len(rwis["properties"].get("cameras", [])) > 0:
                camera_properties = deepcopy(common_properties)
                camera_properties["ref"] = camera_properties["ref"] + "_CAMERA"
                apply_category(Categories.SURVEILLANCE_CAMERA, camera_properties)
                camera_properties["extras"]["contact:webcam"] = ";".join([view["image"] for view in rwis["properties"]["cameras"]])
                if len(rwis["properties"]["cameras"]) > 1:
                    camera_properties["extras"]["camera:type"] = "dome"
                else:
                    camera_properties["extras"]["camera:type"] = "fixed"
                yield Feature(**camera_properties)
