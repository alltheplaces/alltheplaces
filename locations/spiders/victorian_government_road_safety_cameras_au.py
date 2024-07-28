from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_category
from locations.items import Feature


class VictorianGovernmentRoadSafetyCamerasAUSpider(Spider):
    name = "victorian_government_road_safety_cameras_au"
    item_attributes = {"operator": "Department of Justice and Community Safety", "operator_wikidata": "Q5260361"}
    allowed_domains = ["services-ap1.arcgis.com"]
    start_urls = [
        "https://services-ap1.arcgis.com/qP7JqzPTuwJlaCRD/ArcGIS/rest/services/road_safety_camera_network_data_v3/FeatureServer/0/query?where=1%3D1&fullText=&objectIds=&time=&geometry=&geometryType=esriGeometryPoint&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=camera_id%2Ccamera_type%2Csite_type%2Clatitude%2Clongitude%2Coffence_location%2Cintersects_with%2Cstreet%2Csuburb%2Cpostcode&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            if not location.get("geometry"):
                # Some locations returned are 'null' (deleted?) locations.
                continue
            properties = {
                "ref": location["properties"]["camera_id"],
                "geometry": location["geometry"],
                "addr_full": location["properties"]["offence_location"],
                "street": location["properties"]["street"],
                "city": location["properties"]["suburb"],
                "postcode": location["properties"]["postcode"],
                "state": "VIC",
            }

            if location["properties"]["site_type"] == "Intersection":
                apply_category({"highway": "speed_camera", "enforcement": "maxspeed"}, properties)
                apply_category({"highway": "traffic_signals", "enforcement": "traffic_signals"}, properties)
            elif location["properties"]["site_type"] in ["Highway", "Freeway"]:
                apply_category({"highway": "speed_camera", "enforcement": "maxspeed"}, properties)
            elif location["properties"]["site_type"] == "Point-to-point":
                apply_category({"highway": "speed_camera", "enforcement": "average_speed"}, properties)

            yield Feature(**properties)
