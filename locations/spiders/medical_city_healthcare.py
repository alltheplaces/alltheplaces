import json
import re

import scrapy

from locations.categories import Categories, apply_category
from locations.items import Feature


class MedicalCityHealthcareSpider(scrapy.Spider):
    name = "medical_city_healthcare"
    item_attributes = {"brand": "Medical City Healthcare"}
    allowed_domains = ["medicalcityhealthcare.com"]
    start_urls = [
        "https://medicalcityhealthcare.com/locations/",
    ]

    categories = [
        ("Hospital", Categories.HOSPITAL),
        ("Childrens_Hospital", Categories.HOSPITAL),
        ("ER", Categories.HOSPITAL),
        ("Pharmacy", Categories.PHARMACY),
        ("Behavioral_Health", {"healthcare": "psychotherapist", "healthcare:speciality": "behavior"}),
        (
            "Imaging_Center",
            {"amenity": "hospital", "healthcare": "hospital", "healthcare:speciality": "diagnostic_radiology"},
        ),
        ("Surgery_Center", {"amenity": "hospital", "healthcare": "hospital", "healthcare:speciality": "surgery"}),
        ("Rehabilitation_Center", {"healthcare": "rehabilitation"}),
        ("Urgent_Care", Categories.CLINIC_URGENT),
        ("Cancer_Center", {"healthcare": "centre", "healthcare:speciality": "oncology"}),
        ("Health_Center", {"healthcare": "centre"}),
        ("Diagnostic_Center", {"healthcare": "centre"}),
        ("Womens_Center", {"healthcare": "centre"}),
        ("Medical_Group", {"healthcare": "centre"}),
        ("Other", {"healthcare": "centre"}),
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

            types = location.get("type")[1:-1].split(",")
            for label, cat in self.categories:
                if label in types:
                    apply_category(cat, properties)
                    break
            else:
                for cat in types:
                    self.crawler.stats.inc_value(f"atp/medical_city_healthcare/unmatched_category/{cat}")

            yield Feature(**properties)
