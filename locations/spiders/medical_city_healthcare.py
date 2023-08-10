import json
import re

import scrapy

from locations.items import Feature


class MedicalCityHealthcareSpider(scrapy.Spider):
    name = "medical_city_healthcare"
    item_attributes = {"brand": "Medical City Healthcare"}
    allowed_domains = ["medicalcityhealthcare.com"]
    start_urls = [
        "https://medicalcityhealthcare.com/locations/",
    ]

    def parse(self, response):
        script = response.xpath('//script[contains(text(), "hostLocations")]').extract_first()
        data = re.search(r"var hostLocations = (.*]);", script).group(1)
        locations = json.loads(data)

        for location in locations:
            properties = {
                "ref": location["id"],
                "name": location["title"],
                "street_address": location["address1"],
                "city": location["city"],
                "state": location["state"],
                "postcode": location["zip"],
                "lat": location["lat"],
                "lon": location["lng"],
                "phone": location["phone"],
                "website": response.url,
            }

            yield Feature(**properties)
