from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class CityOfSydneyStreetSafetyCamerasAUSpider(Spider):
    name = "city_of_sydney_street_safety_cameras_au"
    item_attributes = {"operator": "City of Sydney", "operator_wikidata": "Q56477532"}
    allowed_domains = ["services1.arcgis.com"]
    start_urls = [
        "https://services1.arcgis.com/cNVyNtjGVZybOQWZ/ArcGIS/rest/services/CCTV_Locations/FeatureServer/0/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryPoint&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=CAMERA_NO%2CPrecinct%2CLocation%2CLocalityPrecinct&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            if not location.get("geometry"):
                continue
            properties = {
                "ref": location["properties"]["CAMERA_NO"],
                "name": location["properties"]["Location"],
                "geometry": location["geometry"],
                "state": "New South Wales",
                "extras": {
                    "surveillance": "public",
                },
            }
            apply_category(Categories.SURVEILLANCE_CAMERA, properties)
            yield Feature(**properties)
