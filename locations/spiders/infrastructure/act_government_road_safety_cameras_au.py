from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_category
from locations.items import Feature


class ActGovernmentRoadSafetyCamerasAUSpider(Spider):
    name = "act_government_road_safety_cameras_au"
    item_attributes = {"operator": "Government of the Australian Capital Territory", "operator_wikidata": "Q27220504"}
    allowed_domains = ["www.data.act.gov.au"]
    start_urls = ["https://www.data.act.gov.au/resource/426s-vdu4.json?$limit=50000"]
    no_refs = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            if not location.get("camera_type"):
                # There are a few features with no tags so we'll just ignore
                # them as they don't seem to provide any value to ATP users.
                continue

            properties = {
                "name": location.get("location_code", location.get("camera_location_code")),
                "addr_full": location.get("location_description"),
                "state": "Australian Capital Territory",
                "lat": location["latitude"],
                "lon": location["longitude"],
            }
            if location["camera_type"] == "FIXED ONLY SPEED CAMERA":
                apply_category({"highway": "speed_camera", "enforcement": "maxspeed"}, properties)
            elif location["camera_type"] == "RED LIGHT AND SPEED CAMERA":
                apply_category({"highway": "speed_camera", "enforcement": "maxspeed"}, properties)
                apply_category({"highway": "traffic_signals", "enforcement": "traffic_signals"}, properties)
            elif location["camera_type"] == "POINT TO POINT CAMERA":
                apply_category({"highway": "speed_camera", "enforcement": "average_speed"}, properties)
            elif location["camera_type"] == "MOBILE SPEED CAMERA":
                apply_category({"highway": "speed_camera", "enforcement": "maxspeed", "permanent": "no"}, properties)
            else:
                self.logger.warning("Unknown traffic camera type: {}".format(location["camera_type"]))

            yield Feature(**properties)
