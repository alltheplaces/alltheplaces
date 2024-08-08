from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_category
from locations.items import Feature


class NswAmbulanceAUSpider(Spider):
    name = "nsw_ambulance_au"
    item_attributes = {"operator": "New South Wales Ambulance", "operator_wikidata": "Q4741948"}
    allowed_domains = ["portal.spatial.nsw.gov.au"]
    start_urls = [
        "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_FOI_Health_Facilities/FeatureServer/0/query?f=geojson"
    ]
    no_refs = True

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["features"]:
            properties = {
                "name": location["properties"]["generalname"],
                "state": "NSW",
                "geometry": location["geometry"],
            }
            if " HEADQUARTERS" in properties["name"]:
                apply_category({"office": "government"}, properties)
                apply_category({"government": "emergency"}, properties)
            elif " HELO AMBULANCE STATION" in properties["name"]:
                apply_category({"emergency": "air_rescue_service"}, properties)
            elif (
                " CFR" in properties["name"] or " VAO" in properties["name"]
            ):  # Community First Responder (CFR) and Volunteer Ambulance Officer (VAO)
                apply_category({"emergency": "first_aid"}, properties)
            else:
                apply_category({"emergency": "ambulance_station"}, properties)
            if properties["name"] in [
                "DICKSON AMBULANCE STATION",
                "GUNGAHLIN AMBULANCE STATION",
                "CALWELL AMBULANCE STATION",
                "PHILLIP AMBULANCE STATION",
                "KAMBAH AMBULANCE STATION",
                "WEST BELCONNEN AMBULANCE STATION",
                "BELCONNEN AMBULANCE STATION",
                "FYSHWICK AMBULANCE STATION",
                "GREENWAY AMBULANCE STATION",
                "SOUTHCARE HELO AMBULANCE STATION",
            ]:
                properties["state"] = "ACT"
                properties["operator"] = "Australian Capital Territory Ambulance Service"
                properties["operator_wikidata"] = "Q4823922"
            yield Feature(**properties)
