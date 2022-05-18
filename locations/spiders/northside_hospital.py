import json
import re
import scrapy
from locations.items import GeojsonPointItem


class NorthsideHospitalSpider(scrapy.Spider):
    name = "northside_hospital"
    item_attributes = {"brand": "Northside Hospital", "brand_wikidata": "Q7059745"}
    allowed_domains = ["www.northside.com"]
    start_urls = ("https://www.northside.com/locations",)

    def start_requests(self):
        template = "https://locations-api.northside.production.merge-digital.com/api/LocationsSearch?Page=1&PageSize=454"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(
            url=template, method="GET", headers=headers, callback=self.parse
        )

    def parse(self, response):
        jsonresponse = response.json()
        for stores in jsonresponse["data"]:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                "name": store_data["name"],
                "ref": store_data["id_string"],
                "addr_full": store_data["address"],
                "city": store_data["city"],
                "state": store_data["state"]["abbreviation"],
                "postcode": store_data["post_code"],
                "phone": store_data["phone_1"],
                "lat": float(store_data["latitude"]),
                "lon": float(store_data["longitude"]),
                "website": store_data["listing_url"],
            }

            yield GeojsonPointItem(**properties)
