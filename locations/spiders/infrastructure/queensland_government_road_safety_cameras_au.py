from chompjs import parse_js_object
from scrapy import Spider

from locations.categories import apply_category
from locations.items import Feature


class QueenslandGovernmentRoadSafetyCamerasAUSpider(Spider):
    name = "queensland_government_road_safety_cameras_au"
    item_attributes = {"operator": "Queensland Government", "operator_wikidata": "Q3112627"}
    allowed_domains = ["www.google.com"]
    start_urls = [
        "https://www.google.com/maps/d/viewer?mid=1KO5byT1dvAbg-wBx8IeAEA7KC2Y&msa=0&ll=-22.677961683728526%2C149.631106&z=6"
    ]
    no_refs = True

    def parse(self, response):
        js_blob = response.xpath('//script[contains(text(), "var _pageData = ")]/text()').get()
        js_blob = js_blob.split('var _pageData = "', 1)[1].split('";', 1)[0]
        js_blob = js_blob.replace('\\"', '"')
        all_cameras = parse_js_object(js_blob)[1][6][0][12][0][13][0]
        for camera in all_cameras:
            properties = {
                "name": camera[5][1][1][0],
                "lat": camera[1][0][0][0],
                "lon": camera[1][0][0][1],
            }
            camera_type = camera[5][0][1][0].replace("Camera type: ", "").replace("\\n", "").strip()
            if camera_type == "red light camera":
                apply_category({"highway": "traffic_signals", "enforcement": "traffic_signals"}, properties)
            elif camera_type == "combined red light/speed camera":
                apply_category({"highway": "speed_camera", "enforcement": "maxspeed"}, properties)
                apply_category({"highway": "traffic_signals", "enforcement": "traffic_signals"}, properties)
            elif camera_type == "Fixed speed camera":
                apply_category({"highway": "speed_camera", "enforcement": "maxspeed"}, properties)
            elif camera_type == "Point-to-point speed camera system":
                apply_category({"highway": "speed_camera", "enforcement": "average_speed"}, properties)
            else:
                self.logger.warning("Unknown type of road safety camera: {}".format(camera_type))
            yield Feature(**properties)
