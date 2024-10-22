import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class MedicalCityHealthcareSpider(scrapy.Spider):
    name = "medical_city_healthcare"
    item_attributes = {"brand": "Medical City Healthcare"}
    allowed_domains = ["medicalcityhealthcare.com"]
    start_urls = [
        "https://medicalcityhealthcare.com/locations/",
    ]

    categories = [
        ("PHYSICIAN PRACTICE", Categories.HOSPITAL),
        ("HOSPITAL - GENERAL", Categories.HOSPITAL),
        ("HOSPITAL - CHILDRENS", Categories.HOSPITAL),
        ("BEHAVIORAL DEPARTMENT", {"healthcare": "psychotherapist", "healthcare:speciality": "behavior"}),
        ("HOSPITAL - PSYCHIATRIC", {"healthcare": "psychotherapist", "healthcare:speciality": "behavior"}),
        (
            "IMAGING CENTER",
            {"amenity": "hospital", "healthcare": "hospital", "healthcare:speciality": "diagnostic_radiology"},
        ),
        ("SURGERY CENTER", {"amenity": "hospital", "healthcare": "hospital", "healthcare:speciality": "surgery"}),
        ("HOSPITAL - REHABILITATION", {"healthcare": "rehabilitation"}),
        ("URGENT CARE CENTER", Categories.CLINIC_URGENT),
        ("CANCER CENTER", {"healthcare": "centre", "healthcare:speciality": "oncology"}),
        ("HEALTH CENTER", {"healthcare": "centre"}),
    ]

    def parse(self, response):
        script = json.loads(response.xpath('//script[@type="application/json"]/text()').get())
        for data in script["sitecore"]["route"]["placeholders"]["body"][0]["placeholders"]["col-top"][0]["fields"][
            "defaultResponse"
        ]["results"]:
            item = DictParser.parse(data)
            item["name"] = data.get("facilityName")
            item["phone"] = data.get("marketedPrimaryPhoneNumber")
            item["website"] = data.get("marketedWebsite")
            item["street_address"] = data.get("street1")
            types = data.get("purposeTypeName")
            item["street"] = types
            for label, cat in self.categories:
                if label in types:
                    apply_category(cat, item)
                    break
            else:
                apply_category(Categories.HOSPITAL, item)
            yield item
