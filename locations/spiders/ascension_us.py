from typing import AsyncIterator

from scrapy.http import JsonRequest
from scrapy.spiders import Spider

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class AscensionUSSpider(Spider):
    name = "ascension_us"
    item_attributes = {"brand": "Ascension", "brand_wikidata": "Q96372437", "nsi_id": "N/A"}
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    _category_map = {
        "Assisted living": (Categories.ASSISTED_LIVING, []),
        "Audiology": (Categories.AUDIOLOGIST, []),
        "Birthing center": (Categories.BIRTHING_CENTRE, []),
        "Cancer care": (Categories.CLINIC, [HealthcareSpecialities.ONCOLOGY]),
        "Cardiac and pulmonary rehab": (
            Categories.CLINIC,
            [
                HealthcareSpecialities.REHABILITATION,
                HealthcareSpecialities.CARDIOLOGY,
                HealthcareSpecialities.PULMONOLOGY,
            ],
        ),
        "Cardiology": (Categories.CLINIC, [HealthcareSpecialities.CARDIOLOGY]),
        "Cosmetic and plastic surgery": (Categories.CLINIC, [HealthcareSpecialities.PLASTIC_SURGERY]),
        "CT": (Categories.MEDICAL_IMAGING, [HealthcareSpecialities.DIAGNOSTIC_RADIOLOGY]),
        "Dermatology": (Categories.CLINIC, [HealthcareSpecialities.DERMATOLOGY]),
        "DEXA scan": (Categories.MEDICAL_IMAGING, [HealthcareSpecialities.DIAGNOSTIC_RADIOLOGY]),
        "Ear, nose and throat care": (Categories.CLINIC, [HealthcareSpecialities.OTOLARYNGOLOGY]),
        "Emergency care": (Categories.HOSPITAL, [HealthcareSpecialities.EMERGENCY]),
        "Emergency care - pediatrics": (
            Categories.HOSPITAL,
            [HealthcareSpecialities.EMERGENCY, HealthcareSpecialities.PAEDIATRICS],
        ),
        "Endocrinology": (Categories.CLINIC, [HealthcareSpecialities.ENDOCRINOLOGY]),
        "Express or urgent care": (Categories.CLINIC_URGENT, []),
        "Gastroenterology": (Categories.CLINIC, [HealthcareSpecialities.GASTROENTEROLOGY]),
        "Geriatric medicine": (Categories.CLINIC, [HealthcareSpecialities.GERIATRICS]),
        "Home health care": (Categories.OFFICE_HEALTHCARE, [HealthcareSpecialities.GERIATRICS]),
        "Hospice care": (Categories.CLINIC, [HealthcareSpecialities.PALLIATIVE]),
        "Hospital/Medical Center": (Categories.HOSPITAL, []),
        "Imaging": (Categories.MEDICAL_IMAGING, [HealthcareSpecialities.DIAGNOSTIC_RADIOLOGY]),
        "Independent living": (Categories.OFFICE_HEALTHCARE, [HealthcareSpecialities.GERIATRICS]),
        "Infeious disease": (
            Categories.CLINIC,
            [HealthcareSpecialities.INFECTIOUS_DISEASES],
        ),  # Typo exists in source data
        "Infectious disease": (Categories.CLINIC, [HealthcareSpecialities.INFECTIOUS_DISEASES]),
        "Inpatient rehabilitation": (Categories.CLINIC, [HealthcareSpecialities.REHABILITATION]),
        "Kidney health": (Categories.CLINIC, [HealthcareSpecialities.NEPHROLOGY]),
        "Laboratory": (Categories.MEDICAL_LABORATORY, []),
        "Mammography": (Categories.MEDICAL_IMAGING, [HealthcareSpecialities.DIAGNOSTIC_RADIOLOGY]),
        "Memory support": (Categories.CLINIC, [HealthcareSpecialities.GERIATRICS]),
        "Mental Health": (Categories.CLINIC, [HealthcareSpecialities.PSYCHIATRY]),
        "MRI": (Categories.MEDICAL_IMAGING, [HealthcareSpecialities.NUCLEAR]),
        "Neurology": (Categories.CLINIC, [HealthcareSpecialities.NEUROLOGY]),
        "Neurosurgery": (Categories.CLINIC, [HealthcareSpecialities.NEUROSURGERY]),
        "Occupational Therapy": (Categories.CLINIC, [HealthcareSpecialities.OCCUPATIONAL]),
        "Occupational Therapy - Pediatrics": (
            Categories.CLINIC,
            [HealthcareSpecialities.OCCUPATIONAL, HealthcareSpecialities.PAEDIATRICS],
        ),
        "Ophthalmology": (Categories.CLINIC, [HealthcareSpecialities.OPHTHALMOLOGY]),
        "Orthopedics": (Categories.CLINIC, [HealthcareSpecialities.ORTHOPAEDICS]),
        "PACE": (Categories.NURSING_HOME, []),
        "Pain management": (Categories.CLINIC, [HealthcareSpecialities.PAIN_MEDICINE]),
        "Palliative": (Categories.CLINIC, [HealthcareSpecialities.PALLIATIVE]),
        "Palliative care": (Categories.CLINIC, [HealthcareSpecialities.PALLIATIVE]),
        "Pediatrics": (Categories.CLINIC, [HealthcareSpecialities.PAEDIATRICS]),
        "Pharmacy": (Categories.PHARMACY, []),
        "Physical Therapy": (Categories.CLINIC, [HealthcareSpecialities.PHYSIATRY]),
        "Podiatry": (Categories.CLINIC, [HealthcareSpecialities.PODIATRY]),
        "Primary Care/Clinic": (Categories.CLINIC, [HealthcareSpecialities.GENERAL]),
        "Pulmonology": (Categories.CLINIC, [HealthcareSpecialities.PULMONOLOGY]),
        "Rehabilitation": (Categories.CLINIC, [HealthcareSpecialities.REHABILITATION]),
        "Rheumatology": (Categories.CLINIC, [HealthcareSpecialities.RHEUMATOLOGY]),
        "Skilled nursing": (Categories.NURSE_CLINIC, []),
        "Sleep disorders": (Categories.CLINIC, [HealthcareSpecialities.SLEEP_MEDICINE]),
        "Speech Therapy - Pediatrics": (Categories.SPEECH_THERAPIST, [HealthcareSpecialities.PAEDIATRICS]),
        "Surgery": (Categories.CLINIC, [HealthcareSpecialities.SURGERY]),
        "Urology": (Categories.CLINIC, [HealthcareSpecialities.UROLOGY]),
        "Weight-loss and bariatric surgery": (Categories.CLINIC, [HealthcareSpecialities.BARIATRIC_SURGERY]),
        "Wellness and fitness": (Categories.CLINIC, [HealthcareSpecialities.GENERAL]),
        "Women's health": (Categories.CLINIC, [HealthcareSpecialities.GYNAECOLOGY]),
        "Wound care and hyperbarics": (Categories.CLINIC, [HealthcareSpecialities.WOUND_TREATMENT]),
        "X-ray": (Categories.MEDICAL_IMAGING, [HealthcareSpecialities.DIAGNOSTIC_RADIOLOGY]),
    }

    @staticmethod
    def make_request(page: int, page_size: int = 100) -> JsonRequest:
        return JsonRequest(
            url="https://healthcare.ascension.org/api/locations/search",
            data={"geoDistanceOptions": {"location": "AL", "radius": 50000}, "page": page, "pageSize": page_size},
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield self.make_request(1)

    def parse(self, response, **kwargs):
        for result in response.json()["Results"]:
            location = result["Data"]["Location"]
            location["Address"]["street_address"] = merge_address_lines(
                [location["Address"].pop("Street"), location["Address"].pop("Street2")]
            )
            item = DictParser.parse(location)
            item["lat"] = location["Address"]["Latitude"]
            item["lon"] = location["Address"]["Longitude"]
            item["website"] = response.urljoin(location["Url"])

            if thumb := location.get("LocationThumbnail"):
                item["image"] = response.urljoin(thumb)

            if location_type_tags := location.get("LocationTypeTags"):
                feature_type = location["LocationTypeTags"][0].strip()
                if cat := self._category_map.get(feature_type):
                    apply_category(cat[0], item)
                    apply_healthcare_specialities(cat[1], item)
                else:
                    self.logger.warning("Unknown category: {}".format(feature_type))
                    apply_category(Categories.CLINIC, item)  # Fallback category
            else:
                apply_category(Categories.CLINIC, item)

            yield item

        pagination = response.json()["Pagination"]
        if pagination["CurrentPage"] < pagination["TotalPages"]:
            yield self.make_request(pagination["CurrentPage"] + 1)
