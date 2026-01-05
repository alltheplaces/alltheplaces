from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import (
    Categories,
    HealthcareSpecialities,
    apply_category,
    apply_healthcare_specialities,
    apply_yes_no,
)
from locations.dict_parser import DictParser

HEALTHCARE_CATEGORIES = {
    "Anticoagulation Clinics": [Categories.CLINIC],
    "Audiology": [Categories.AUDIOLOGIST],
    "Bariatrics and Weight Loss": [Categories.CLINIC, HealthcareSpecialities.BARIATRIC_SURGERY],
    "Behavioral and Mental Health": [Categories.PSYCHOTHERAPIST, HealthcareSpecialities.PSYCHOTHERAPHY_BEHAVIOR],
    "Breast Health Centers": [Categories.CLINIC, HealthcareSpecialities.ONCOLOGY],
    "Cancer Care and Oncology": [Categories.CLINIC, HealthcareSpecialities.ONCOLOGY],
    "Dermatology": [Categories.CLINIC, HealthcareSpecialities.DERMATOLOGY],
    "Endocrinology and Diabetes": [Categories.CLINIC, HealthcareSpecialities.ENDOCRINOLOGY],
    "Ear, Nose and Throat (ENT)": [Categories.CLINIC, HealthcareSpecialities.OTOLARYNGOLOGY],
    "Emergency Care": [Categories.EMERGENCY_WARD],
    "Fitness Centers": [Categories.GYM],
    "General Surgery": [Categories.CLINIC, HealthcareSpecialities.SURGERY],
    "Surgery Centers": [Categories.CLINIC, HealthcareSpecialities.SURGERY],
    "Geriatrics Senior Care": [Categories.CLINIC, HealthcareSpecialities.GERIATRICS],
    "Gastroenterology, Liver and Pancreas": [Categories.CLINIC, HealthcareSpecialities.GASTROENTEROLOGY],
    "Gynecology and OB/GYN": [Categories.CLINIC, HealthcareSpecialities.GYNAECOLOGY],
    "Women's Health Centers": [Categories.CLINIC, HealthcareSpecialities.GYNAECOLOGY],
    "Heart and Vascular Care": [Categories.CLINIC, HealthcareSpecialities.CARDIOLOGY],
    "Home Health Care": [Categories.CLINIC],
    "Hospice Care": [Categories.HOSPICE],
    "Hospitals": [Categories.HOSPITAL],
    "Infectious Diseases": [Categories.CLINIC, HealthcareSpecialities.INFECTIOUS_DISEASES],
    "Imaging and Radiology": [Categories.MEDICAL_LABORATORY],
    "Lab Services": [Categories.MEDICAL_LABORATORY],
    "Maternity and Birthing Centers": [Categories.BIRTHING_CENTRE],
    "Medical Centers and Clinics": [Categories.CLINIC],
    "Dialysis and Kidney Care": [Categories.CLINIC, HealthcareSpecialities.NEPHROLOGY],
    "Neurology and Neurosurgery": [
        Categories.CLINIC,
        HealthcareSpecialities.NEUROLOGY,
        HealthcareSpecialities.NEUROSURGERY,
    ],
    "Occupational Health": [Categories.CLINIC, HealthcareSpecialities.OCCUPATIONAL],
    "Orthopedics and Sports Medicine": [Categories.CLINIC, HealthcareSpecialities.ORTHOPAEDICS],
    "Other Locations": [Categories.CLINIC],
    "Pain Management": [Categories.CLINIC, HealthcareSpecialities.PAIN_MEDICINE],
    "Pediatrics": [Categories.CLINIC, HealthcareSpecialities.PAEDIATRICS],
    "Pharmacy Locations": [Categories.PHARMACY],
    "Physical Therapy and Rehabilitation": [Categories.REHABILITATION, HealthcareSpecialities.REHABILITATION],
    "Podiatry": [Categories.CLINIC, HealthcareSpecialities.PODIATRY],
    "Primary Care and Family Medicine": [Categories.DOCTOR_GP],
    "Pulmonary and Sleep Medicine": [Categories.CLINIC, HealthcareSpecialities.PULMONOLOGY],
    "Plastic & Reconstructive Surgery": [Categories.CLINIC, HealthcareSpecialities.PLASTIC_SURGERY],
    "Rheumatology": [Categories.CLINIC, HealthcareSpecialities.RHEUMATOLOGY],
    "School-Based Health": [Categories.CLINIC],
    "Senior Living": [Categories.NURSING_HOME],
    "Sleep Medicine": [Categories.CLINIC, HealthcareSpecialities.SLEEP_MEDICINE],
    "Urgent Care": [Categories.CLINIC_URGENT],
    "Urology Care": [Categories.CLINIC, HealthcareSpecialities.UROLOGY],
    "Vein Therapy": [Categories.CLINIC, HealthcareSpecialities.VASCULAR_SURGERY],
    "Walk-In Health Care Clinics": [Categories.CLINIC_URGENT],
    "Wound Care Centers": [Categories.CLINIC, HealthcareSpecialities.WOUND_TREATMENT],
}


class MercyHealthUSSpider(Spider):
    name = "mercy_health_us"
    item_attributes = {"operator": "Mercy Health", "operator_wikidata": "Q5053169"}
    start_urls = ["https://www.mercy.com/api/v2/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location_info in response.json()["Results"]:
            location = location_info["Location"]
            item = DictParser.parse(location)
            item["street_address"] = location["Address"]["StreetDisplay"]
            item["website"] = response.urljoin(location["Link"])
            if "/podiatry-foot-care/" in item["website"]:
                facility_type = "Podiatry"
            elif "/sleep-medicine-sleep-centers/" in item["website"]:
                facility_type = "Sleep Medicine"
            elif "/vein-therapy/" in item["website"]:
                facility_type = "Vein Therapy"
            else:
                facility_type = location.get("FacilityType", {}).get("Name")
            if category := HEALTHCARE_CATEGORIES.get(facility_type):
                for tags in category:
                    if isinstance(tags, Categories):
                        apply_category(tags, item)
                    elif isinstance(tags, HealthcareSpecialities):
                        apply_healthcare_specialities([tags], item)
                if facility_type == "Home Health Care":
                    apply_yes_no("home_visit", item, True)
            else:
                self.crawler.stats.inc_value(f"atp/{self.name}/unmapped_category/{facility_type}")
            yield item
