from scrapy import Selector, Spider
from scrapy.http import FormRequest

from locations.geo import point_locations
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


class PetsAtHomeGBSpider(Spider):
    name = "petsathome_gb"
    item_attributes = {"brand": "Pets at Home", "brand_wikidata": "Q7179258"}
    wanted_types = ["PetStore"]

    def start_requests(self):
        for lat, lon in point_locations("eu_centroids_20km_radius_country.csv", "UK"):
            yield FormRequest(
                url="https://community.petsathome.com/models/utils.cfc",
                formdata={
                    "method": "functionhandler",
                    "returnFormat": "json",
                    "event": "webproperty.storelocator",
                    "lat": str(lat),
                    "lng": str(lon),
                    "radius": "50000",
                    "companyID": "E25254CF-02A9-4666-9722-C6CC3E6DD402",
                    "active": "true",
                },
                headers={"X-Requested-With": "XMLHttpRequest"},
            )

    def parse(self, response):
        for node in response.json()["data"]:
            ld = MicrodataParser.convert_to_graph(MicrodataParser.extract_microdata(Selector(text=node["microdata"])))
            item = LinkedDataParser.parse_ld(ld)

            item["ref"] = item["website"] = f'https://community.petsathome.com{node["slug"]}'
            item["lat"] = node["lat"]
            item["lon"] = node["lng"]
            item["addr_full"] = node["formattedaddress"]
            # TODO: opentimes

            yield item
