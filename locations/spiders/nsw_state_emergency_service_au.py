from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import apply_category
from locations.items import Feature


class NswStateEmergencyServiceAUSpider(Spider):
    name = "nsw_state_emergency_service_au"
    item_attributes = {"operator": "New South Wales State Emergency Service", "operator_wikidata": "Q7011790"}
    allowed_domains = ["portal.spatial.nsw.gov.au"]
    start_urls = [
        "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_FOI_Emergency_Service_Facilities/FeatureServer/3/query?f=geojson"
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
            if properties["name"][:4] == "ACT ":
                properties["state"] = "ACT"
            if " HEADQUARTERS" in properties["name"]:
                apply_category({"office": "government"}, properties)
                apply_category({"government": "emergency"}, properties)
            elif "MARINE RESCUE " in properties["name"]:
                apply_category({"emergency": "water_rescue"}, properties)
            elif (
                " SES" in properties["name"]
                or " MINES RESCUE STATION" in properties["name"]
                or ("ACT ESA " in properties["name"] and " UNIT" in properties["name"])
            ):
                apply_category({"amenity": "rescue_station"}, properties)
            else:
                apply_category({"office": "government"}, properties)
                apply_category({"government": "emergency"}, properties)
            yield Feature(**properties)
