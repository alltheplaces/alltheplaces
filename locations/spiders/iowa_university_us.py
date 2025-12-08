from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import Response

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.items import Feature
from locations.storefinders.algolia import AlgoliaSpider

specialty_map = {
    "Allergy and Immunology": HealthcareSpecialities.ALLERGOLOGY,
    "Anesthesia": HealthcareSpecialities.ANAESTHETICS,
    "Burn Treatment": HealthcareSpecialities.PLASTIC_SURGERY,
    "Cancer": HealthcareSpecialities.ONCOLOGY,
    "Cancer and Blood Disease": HealthcareSpecialities.HAEMATOLOGY,
    "Cardiology": HealthcareSpecialities.CARDIOLOGY,
    "Critical Care": HealthcareSpecialities.ANAESTHETICS,
    "Department of Pediatrics": HealthcareSpecialities.PAEDIATRICS,
    "Emergency Medicine": HealthcareSpecialities.EMERGENCY,
    "Endocrinology": HealthcareSpecialities.ENDOCRINOLOGY,
    "Family Medicine": HealthcareSpecialities.COMMUNITY,
    "Gastroenterology": HealthcareSpecialities.GASTROENTEROLOGY,
    "General Pediatrics (Pediatricians)": HealthcareSpecialities.PAEDIATRICS,
    "Heart and Vascular": HealthcareSpecialities.CARDIOLOGY,
    "Infectious Diseases": HealthcareSpecialities.INFECTIOUS_DISEASES,
    "Lung Services": HealthcareSpecialities.PULMONOLOGY,
    "Neonatology": HealthcareSpecialities.NEONATOLOGY,
    "Nephrology": HealthcareSpecialities.NEPHROLOGY,
    "Neurology": HealthcareSpecialities.NEUROLOGY,
    "Neurosurgery": HealthcareSpecialities.NEUROSURGERY,
    "Obstetrics and Gynecology": HealthcareSpecialities.GYNAECOLOGY,
    "Obstetrics and Gynecology (OBGYN)": HealthcareSpecialities.GYNAECOLOGY,
    "Ophthalmology and Visual Sciences": HealthcareSpecialities.OPHTHALMOLOGY,
    "Orthopedics and Rehabilitation": HealthcareSpecialities.ORTHOPAEDICS,
    "Otolaryngology - Head and Neck Surgery": HealthcareSpecialities.OTOLARYNGOLOGY,
    "Pathology": HealthcareSpecialities.PATHOLOGY,
    "Primary Care": HealthcareSpecialities.COMMUNITY,
    "Psychiatry": HealthcareSpecialities.PSYCHIATRY,
    "Psychology": HealthcareSpecialities.PSYCHIATRY,
    "Pulmonology": HealthcareSpecialities.PULMONOLOGY,
    "Radiology": HealthcareSpecialities.RADIOLOGY,
    "Rheumatology": HealthcareSpecialities.RHEUMATOLOGY,
    "Surgery": HealthcareSpecialities.SURGERY,
    "Transplant": HealthcareSpecialities.TRANSPLANT,
    "Urology": HealthcareSpecialities.UROLOGY,
}


class IowaUniversityUSSpider(AlgoliaSpider):
    name = "iowa_university_us"
    item_attributes = {
        "brand": "University of Iowa Hospitals and Clinics",
        "brand_wikidata": "Q7895561",
    }
    app_id = "6X6RKBA85V"
    api_key = "28a56450886fd9b7df4a5572130dba6b"
    index_name = "new_uihc_locations_asc"
    referer = "https://uihc.org/locations"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["ref"] = feature["objectID"]
        item["state"] = feature["administrative_area"]
        item["website"] = urljoin(self.referer, item["website"])

        if image := feature.get("image"):
            item["image"] = urljoin(self.referer, image)

        services = feature.get("location_service", [])
        if "Same-Day Care" in services:
            apply_category(Categories.CLINIC, item)
        else:
            apply_category(Categories.HOSPITAL, item)
        apply_healthcare_specialities(
            {specialty_map[service] for service in services if service in specialty_map}, item
        )

        yield item
