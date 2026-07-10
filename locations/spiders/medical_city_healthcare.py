from json import loads
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.hours import OpeningHours, DAYS_FROM_SUNDAY
from locations.items import Feature
from locations.dict_parser import DictParser


class MedicalCityHealthcareSpider(Spider):
    name = "medical_city_healthcare"
    item_attributes = {"brand": "Medical City Healthcare", "brand_wikidata": "Q140420893"}
    allowed_domains = ["www.medicalcityhealthcare.com"]
    start_urls = ["https://www.medicalcityhealthcare.com/locations"]

    categories = {
        "PHYSICIAN PRACTICE": (Categories.CLINIC, [HealthcareSpecialities.GENERAL]),
        "HOSPITAL - GENERAL": (Categories.HOSPITAL, []),
        "HOSPITAL - CHILDRENS": (Categories.HOSPITAL, [HealthcareSpecialities.PAEDIATRICS]),
        "HOSPITAL - OTHER": (Categories.HOSPITAL, []),
        "BEHAVIORAL DEPARTMENT": (Categories.HOSPITAL, [HealthcareSpecialities.PSYCHOTHERAPHY_BEHAVIOR]),
        "HOSPITAL - PSYCHIATRIC": (Categories.HOSPITAL, [HealthcareSpecialities.PSYCHIATRY]),
        "IMAGING CENTER": (Categories.MEDICAL_IMAGING, [HealthcareSpecialities.DIAGNOSTIC_RADIOLOGY]),
        "IMAGING DEPARTMENT": (Categories.HOSPITAL, [HealthcareSpecialities.DIAGNOSTIC_RADIOLOGY]),
        "SURGERY CENTER": (Categories.HOSPITAL, [HealthcareSpecialities.SURGERY]),
        "AMBULATORY SURGERY CENTER": (Categories.HOSPITAL, [HealthcareSpecialities.SURGERY]),
        "HOSPITAL - REHABILITATION": (Categories.HOSPITAL, [HealthcareSpecialities.REHABILITATION]),
        "URGENT CARE CENTER": (Categories.CLINIC_URGENT, []),
        "FREE STANDING EMERGENCY ROOM": (Categories.HOSPITAL, [HealthcareSpecialities.EMERGENCY]),
        "CANCER CENTER": (Categories.CLINIC, [HealthcareSpecialities.ONCOLOGY]),
        "HEALTH CENTER": (Categories.CLINIC, []),
        "HEALTH CENTER DEPARTMENT": (Categories.CLINIC, []),
    }

    def parse(self, response: Response) -> Iterable[Feature]:
        next_data = loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())
        features = next_data["props"]["pageProps"]["layoutData"]["sitecore"]["route"]["placeholders"]["body"][0]["placeholders"]["col-top"][0]["fields"]["defaultResponse"]["results"]
        for feature in features:
            item = DictParser.parse(feature)
            item["name"] = feature.get("facilityName")
            item["phone"] = feature.get("marketedPrimaryPhoneNumber")
            item["website"] = feature.get("marketedWebsite")
            item["street_address"] = feature.get("street1")

            if facility_hours := feature.get("marketedFacilityHours"):
                item["opening_hours"] = OpeningHours()
                for day_number, day_hours in enumerate(facility_hours):
                    day_name = DAYS_FROM_SUNDAY[day_number]
                    if not day_hours:
                        item["opening_hours"].set_closed(day_name)
                    else:
                        open_time = day_hours["open"]
                        close_time = day_hours["close"]
                        item["opening_hours"].add_range(day_name, open_time, close_time)

            if facility_type := feature.get("purposeTypeName"):
                if facility_type in self.categories.keys():
                    apply_category(self.categories[facility_type][0], item)
                    if specialities := self.categories[facility_type][1]:
                        apply_healthcare_specialities(specialities, item)
                else:
                    self.logger.warning("Unknown facility type: {}".format(facility_type))
                    self.crawler.stats.inc_value(f"atp/medical_city_healthcare/unmatched_category/{facility_type}")

            yield item
