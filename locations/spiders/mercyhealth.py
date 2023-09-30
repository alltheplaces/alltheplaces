import json

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature

AMENITIES = {
    "": Categories.HOSPITAL,
    "DiagnosticLab": {"healthcare": "laboratory"},
    "EmergencyService": {"emergency": "emergency_ward_entrance"},
    "ExerciseGym": {"leisure": "fitness_centre"},
    "Hospital": Categories.HOSPITAL,
    "MedicalClinic": {"amenity": "clinic"},
    "Pharmacy": {"amenity": "pharmacy"},
    "ProfessionalService": Categories.HOSPITAL,
    "Residence": {"social_facility": "nursing_home"},
}


class MercyHealthSpider(scrapy.Spider):
    name = "mercyhealth"
    item_attributes = {"brand": "Mercy Health", "brand_wikidata": "Q5053169"}
    allowed_domains = ["www.mercy.com"]
    start_urls = [
        "https://www.mercy.com/locations",
    ]

    def start_requests(self):
        template = "https://www.mercy.com/api/v1/locations"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(url=template, method="GET", headers=headers, callback=self.parse)

    def parse(self, response):
        jsonresponse = response.json()
        for stores in jsonresponse["Results"]:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                "name": store_data["Location"]["Name"],
                "ref": store_data["Location"]["KyruusId"],
                "street_address": store_data["Location"]["Address"]["Street1"],
                "city": store_data["Location"]["Address"]["City"],
                "state": store_data["Location"]["Address"]["State"],
                "postcode": store_data["Location"]["Address"]["PostalCode"],
                "phone": store_data["Location"]["Phone"],
                "lat": float(store_data["Location"]["Latitude"]),
                "lon": float(store_data["Location"]["Longitude"]),
                "website": store_data["Location"]["Link"],
            }

            item = Feature(**properties)
            facility_type = store_data.get("Location", {}).get("FacilityType", {}).get("SchemaPlaceType", "")
            apply_category(AMENITIES[facility_type], item)
            yield item
