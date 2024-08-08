import json

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class PetParadiseSpider(scrapy.Spider):
    name = "pet_paradise"
    item_attributes = {"brand": "Pet Paradise", "brand_wikidata": "Q122955413"}
    allowed_domains = ["petparadise.com"]
    start_urls = ("https://www.petparadise.com/locations.htm",)

    def start_requests(self):
        url = "https://www.petparadise.com/files/4859/widget856515.js"

        headers = {
            "Accept": "application/javascript",
        }

        yield scrapy.http.FormRequest(url=url, method="GET", headers=headers, callback=self.parse)

    def parse(self, response):
        text1 = response.text
        text2 = text1.lstrip("widget856515DataCallback (")
        text = text2.rstrip(");")
        data = json.loads(text)

        for stores in data["PropertyorInterestPoint"]:
            store = json.dumps(stores)
            store_data = json.loads(store)

            properties = {
                "ref": store_data["interestpointpropertyname"],
                "name": store_data["interestpointpropertyname"],
                "street_address": store_data["interestpointpropertyaddress"],
                "city": store_data["interestpointCity"],
                "state": store_data["interestpointState"],
                "postcode": store_data["interestpointPostalCode"],
                "phone": store_data["interestpointPhoneNumber"],
                "lat": float(store_data["interestpointinterestlatitude"]),
                "lon": float(store_data["interestpointinterestlongitude"]),
                "website": store_data["interestpointMoreInfoLink"],
            }

            apply_category(Categories.ANIMAL_BOARDING, properties)
            yield Feature(**properties)
