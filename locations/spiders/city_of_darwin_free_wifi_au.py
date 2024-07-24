from json import loads

from scrapy import Spider
from scrapy.http import JsonRequest
from shapely import to_geojson
from shapely.geometry import Polygon, shape

from locations.categories import Categories, apply_category
from locations.items import Feature


class CityOfDarwinFreeWifiAUSpider(Spider):
    name = "city_of_darwin_free_wifi_au"
    item_attributes = {"operator": "City of Darwin", "operator_wikidata": "Q125673118"}
    allowed_domains = ["services6.arcgis.com"]
    start_urls = [
        "https://services6.arcgis.com/tVfesLETUHNU9Vna/ArcGIS/rest/services/Public_Wifi_APs_and_Coverage/FeatureServer/5/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryPoint&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=Hotspot_Name%2CPrecinct%2CShape__Length&returnGeometry=true&returnCentroid=false&returnEnvelope=false&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
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
                "geometry": loads(to_geojson(Polygon(shape(location["geometry"])).centroid)),
                "state": "Northern Territory",
                "extras": {
                    "internet_access": "wlan",
                    "internet_access:fee": "no",
                    "internet_access:operator": "Telstra",
                    "internet_access:operator:wikidata": "Q721162",
                    "internet_access:ssid": "City of Darwin Free Wi-Fi",
                },
            }
            apply_category(Categories.ANTENNA, properties)

            yield Feature(**properties)
