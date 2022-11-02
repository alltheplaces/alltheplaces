import scrapy
from scrapy.http import FormRequest

from locations.geo import point_locations
from locations.structured_data_spider import StructuredDataSpider


class PetsAtHomeGBSpider(StructuredDataSpider):
    name = "petsathome_gb"
    item_attributes = {"brand": "Pets at Home", "brand_wikidata": "Q7179258"}
    wanted_types = ["PetStore"]
    download_delay = 0.2

    def start_requests(self):
        for (lat, lon) in point_locations("eu_centroids_20km_radius_country.csv", "UK"):
            yield FormRequest(
                url="https://community.petsathome.com/models/utils.cfc",
                formdata={
                    "method": "functionhandler",
                    "returnFormat": "json",
                    "event": "webproperty.storelocator",
                    "lat": str(lat),
                    "lng": str(lon),
                    "radius": "50",
                    "companyID": "any",
                    "active": "true",
                },
                headers={"X-Requested-With": "XMLHttpRequest"},
            )

    def parse(self, response):
        for node in response.json()["data"]:
            if "groom-room" not in node["slug"]:
                website_url = "https://community.petsathome.com" + node["slug"]
                yield scrapy.Request(website_url, callback=self.parse_sd)
