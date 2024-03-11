from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.items import Feature


class NSWRuralFireServiceAUSpider(Spider):
    name = "nsw_rural_fire_service_au"
    item_attributes = {"brand": "New South Wales Rural Fire Service", "brand_wikidata": "Q7011777"}
    allowed_domains = ["portal.spatial.nsw.gov.au"]
    start_urls = [
        "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_FOI_Emergency_Service_Facilities/FeatureServer/2/query?f=geojson"
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
            if "ACT RFS " in properties["name"]:
                properties["state"] = "ACT"
            if (
                " RFB" in properties["name"]
                or " FIRE CONTROL CENTRE" in properties["name"]
                or "ACT RFS " in properties["name"]
            ):
                apply_category(Categories.FIRE_STATION, properties)
            else:
                apply_category({"office": "government"}, properties)
                apply_category({"government": "fire_service"}, properties)
            yield Feature(**properties)
