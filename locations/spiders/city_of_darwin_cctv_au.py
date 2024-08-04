from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class CityOfDarwinCctvAUSpider(Spider):
    name = "city_of_darwin_cctv_au"
    item_attributes = {"operator": "City of Darwin", "operator_wikidata": "Q125673118"}
    allowed_domains = ["services6.arcgis.com"]
    start_urls = [
        "https://services6.arcgis.com/tVfesLETUHNU9Vna/ArcGIS/rest/services/CCTV_Points/FeatureServer/0/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryPoint&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=CameraID%2CDescription%2CCamera_Type%2CDirection%2COwner&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
    ]
    no_refs = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            if not location.get("geometry"):
                continue
            properties = {
                "name": location["properties"].get("Description"),
                "geometry": location["geometry"],
                "state": "Northern Territory",
                "extras": {
                    "surveillance": "public",
                },
            }

            if location["properties"].get("Camera_Type") != "Fixed":
                self.logger.warning("Unknown camera type: {}".format(location["properties"].get("Camera_Type")))
            else:
                properties["extras"]["camera:type"] = "fixed"
                if location["properties"].get("Direction"):
                    direction_angle = int(location["properties"].get("Direction"))
                    if direction_angle < 0:
                        direction_angle = 360 + direction_angle
                    properties["extras"]["camera:direction"] = str(direction_angle)

            apply_category(Categories.SURVEILLANCE_CAMERA, properties)

            yield Feature(**properties)
