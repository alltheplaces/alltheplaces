import scrapy

from locations.categories import apply_category
from locations.items import Feature


class VoyageCareSpider(scrapy.Spider):
    name = "voyage_care"
    item_attributes = {"brand": "Voyage Care"}
    allowed_domains = ["voyagecare.com"]
    start_urls = [
        "https://www.voyagecare.com/in-your-area/",
    ]

    def start_requests(self):
        template = "https://www.voyagecare.com/wp-json/voyagecare/v1/services/null/null/null/null/0/0/500"

        headers = {
            "Accept": "application/json",
        }

        yield scrapy.http.FormRequest(url=template, method="GET", headers=headers, callback=self.parse)

    def parse(self, response):
        jsondata = response.json()
        data = jsondata["body"]
        for store in data:
            properties = {
                "ref": store["properties"]["id"],
                "name": store["properties"]["post_title"],
                "country": "UK",
                "addr_full": store["properties"]["address1_line1"],
                "city": store["properties"]["address1_city"],
                "state": store["properties"]["address1_stateorprovince"],
                "postcode": store["properties"]["address1_postalcode"],
                "lat": float(store["properties"]["address1_latitude"]),
                "lon": float(store["properties"]["address1_longitude"]),
                "website": response.url,
            }
            apply_category({"amenity": "social_facility", "social_facility:for": "disabled"}, properties)
            yield Feature(**properties)
