from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class VicFreeWifiAUSpider(Spider):
    name = "vic_free_wifi_au"
    item_attributes = {"operator": "Victorian State Government", "operator_wikidata": "Q5589335"}
    allowed_domains = ["services-ap1.arcgis.com"]
    start_urls = [
        "https://services-ap1.arcgis.com/qP7JqzPTuwJlaCRD/ArcGIS/rest/services/vicfreewifi/FeatureServer/0/query?where=1%3D1&objectIds=&time=&geometry=&geometryType=esriGeometryPoint&inSR=&spatialRel=esriSpatialRelIntersects&resultType=none&distance=0.0&units=esriSRUnit_Meter&relationParam=&returnGeodetic=false&outFields=Name%2CLong_Name%2CStatus%2CLocation_details&returnGeometry=true&featureEncoding=esriDefault&multipatchOption=xyFootprint&maxAllowableOffset=&geometryPrecision=&outSR=&defaultSR=&datumTransformation=&applyVCSProjection=false&returnIdsOnly=false&returnUniqueIdsOnly=false&returnCountOnly=false&returnExtentOnly=false&returnQueryGeometry=false&returnDistinctValues=false&cacheHint=false&orderByFields=&groupByFieldsForStatistics=&outStatistics=&having=&resultOffset=&resultRecordCount=&returnZ=false&returnM=false&returnExceededLimitFeatures=true&quantizationParameters=&sqlFormat=none&f=pgeojson&token="
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            if not location.get("geometry"):
                continue
            properties = {
                "ref": location["properties"]["Name"],
                "geometry": location["geometry"],
                "name": location["properties"]["Long_Name"],
                "addr_full": location["properties"]["Location_details"],
                "extras": {
                    "internet_access": "wlan",
                    "internet_access:fee": "no",
                    "internet_access:operator": "TPG Telecom",
                    "internet_access:operator:wikidata": "Q7939276",
                    "internet_access:ssid": "VicFreeWiFi",
                },
            }
            apply_category(Categories.ANTENNA, properties)
            yield Feature(**properties)
