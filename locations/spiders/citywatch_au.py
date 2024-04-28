from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class CityWatchAUSpider(Spider):
    name = "citywatch_au"
    item_attributes = {"operator": "City of Perth", "operator_wikidata": "Q1855330"}
    allowed_domains = ["services7.arcgis.com"]
    start_urls = [
        "https://services7.arcgis.com/v8XBa2naYNQGOjlG/ArcGIS/rest/services/INF_AST_SECURITYCAMERAS_PV/FeatureServer/0/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryPoint&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=CAMERA_NUM&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            if not location.get("geometry"):
                continue
            properties = {
                "ref": location["properties"]["CAMERA_NUM"],
                "geometry": location["geometry"],
                "state": "Western Australia",
                "extras": {
                    "surveillance": "public",
                },
            }
            apply_category(Categories.SURVEILLANCE_CAMERA, properties)
            yield Feature(**properties)
