from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.categories import Categories, HealthcareSpecialities, apply_healthcare_specialities
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class RamsayHealthCareAUSpider(JSONBlobSpider):
    name = "ramsay_health_care_au"
    item_attributes = {
        "operator": "Ramsay Health Care",
        "operator_wikidata": "Q17054333",
        "extras": Categories.HOSPITAL.value,
    }
    allowed_domains = ["www.ramsayhealth.com.au"]
    start_urls = ["https://www.ramsayhealth.com.au/Find-a-Service/Hospitals"]

    def extract_json(self, response: Response) -> list[dict]:
        js_blob = response.xpath('//script[contains(text(), "const initialHospitals = ")]/text()').get()
        js_blob = js_blob.split("const initialHospitals = ", 1)[1].splitlines()[0]
        return parse_js_object(js_blob)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("HospitalId")
        item["name"] = feature.get("HospitalName")
        item["street_address"] = merge_address_lines([feature.get("Address1"), feature.get("Address2")])
        if isinstance(item["postcode"], int):
            item["postcode"] = str(item["postcode"])
        item["website"] = feature.get("Web")

        specialities_mapping = {
            "After Hours GP": HealthcareSpecialities.GENERAL,
            "Aged Care and Rehabilitation": HealthcareSpecialities.GERIATRICS,
            "Allergy": HealthcareSpecialities.ALLERGOLOGY,
            "Anaesthetics": HealthcareSpecialities.ANAESTHETICS,
            "Bariatric - Obesity Surgery": HealthcareSpecialities.BARIATRIC_SURGERY,
            "Breast Cancer": HealthcareSpecialities.ONCOLOGY,
            "Breast Surgery": HealthcareSpecialities.SURGERY,
            "Cardiac Surgery": HealthcareSpecialities.CARDIOTHORACIC_SURGERY,
            "Cardiology": HealthcareSpecialities.CARDIOLOGY,
            "Cardiology - Interventional": HealthcareSpecialities.CARDIOLOGY,
            "Cardio-Thoracic Surgery": HealthcareSpecialities.CARDIOTHORACIC_SURGERY,
            "Colorectal Surgery": HealthcareSpecialities.PROCTOLOGY,
            "Dental Surgery": HealthcareSpecialities.PERIODONTICS,
            "Dermatology": HealthcareSpecialities.DERMATOLOGY,
            "Ear Nose and Throat": HealthcareSpecialities.OTOLARYNGOLOGY,
            "Emergency Department": HealthcareSpecialities.EMERGENCY,
            "Emergency Medicine": HealthcareSpecialities.EMERGENCY,
            "Endocrine Surgery": HealthcareSpecialities.ENDOCRINOLOGY,
            "Endocrinology": HealthcareSpecialities.ENDOCRINOLOGY,
            "Fertility - IVF": HealthcareSpecialities.FERTILITY,
            "Fetal Medicine": None,
            "Gastroenterology": HealthcareSpecialities.GASTROENTEROLOGY,
            "General Medicine": HealthcareSpecialities.GENERAL,
            "General Surgery": HealthcareSpecialities.SURGERY,
            "Genetics": None,
            "Geriatric Medicine": HealthcareSpecialities.GERIATRICS,
            "Gynaecological Oncology": HealthcareSpecialities.GYNAECOLOGY,
            "Gynaecology": HealthcareSpecialities.GYNAECOLOGY,
            "Haematology": HealthcareSpecialities.HAEMATOLOGY,
            "Head and Neck Surgery": HealthcareSpecialities.OTOLARYNGOLOGY,
            "Hepatic and Biliary Surgery": HealthcareSpecialities.HEPATOLOGY,
            "Hepatology": HealthcareSpecialities.HEPATOLOGY,
            "Hepato-Pancreato-Biliary Surgery": HealthcareSpecialities.HEPATOLOGY,
            "Hypertension": None,
            "Immunology and Allergy": HealthcareSpecialities.ALLERGOLOGY,
            "Infectious Diseases": HealthcareSpecialities.INFECTIOUS_DISEASES,
            "Intensive Care Unit": HealthcareSpecialities.INTENSIVE,
            "Intensivists": HealthcareSpecialities.INTENSIVE,
            "Interventional Neuroradiology": HealthcareSpecialities.RADIOLOGY,
            "Interventional Radiology": HealthcareSpecialities.RADIOTHERAPY,
            "Medical Oncology": HealthcareSpecialities.ONCOLOGY,
            "Neonatology": HealthcareSpecialities.NEONATOLOGY,
            "Nephrology": HealthcareSpecialities.NEPHROLOGY,
            "Neurology": HealthcareSpecialities.NEUROLOGY,
            "Neurophysiology": HealthcareSpecialities.NEUROPSYCHIATRY,
            "Neurosurgery": HealthcareSpecialities.NEUROSURGERY,
            "Neurosurgery - Spine": HealthcareSpecialities.NEUROSURGERY,
            "Nuclear Medicine": HealthcareSpecialities.NUCLEAR,
            "Obstetric Medicine": HealthcareSpecialities.GYNAECOLOGY,
            "Obstetrics and Gynaecology": HealthcareSpecialities.GYNAECOLOGY,
            "Obstetrics": HealthcareSpecialities.GYNAECOLOGY,
            "Oncology": HealthcareSpecialities.ONCOLOGY,
            "Ophthalmology": HealthcareSpecialities.OPHTHALMOLOGY,
            "Ophthalmology - Paediatric": HealthcareSpecialities.PAEDIATRICS,
            "Oral and Maxillofacial Surgery": HealthcareSpecialities.MAXILLOFACIAL,
            "Oral Surgery": HealthcareSpecialities.STOMATOLOGY,
            "Orthopaedic Surgery - Elbow": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Foot and Ankle": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Hand": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Hip and Knee": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Hip": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Knee": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Paediatric": HealthcareSpecialities.PAEDIATRIC_SURGERY,
            "Orthopaedic Surgery - Shoulder and Knee": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Shoulder and Upper Limb": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Shoulder": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Shoulder": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Spine": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Sports Injury": HealthcareSpecialities.ORTHOPAEDICS,
            "Orthopaedic Surgery - Upper Limb": HealthcareSpecialities.ORTHOPAEDICS,
            "Otolaryngology - Head and Neck": HealthcareSpecialities.OTOLARYNGOLOGY,
            "Paediatric Dentistry": HealthcareSpecialities.PAEDIATRIC_DENTISTRY,
            "Paediatric Endocrinology": HealthcareSpecialities.PAEDIATRICS,
            "Paediatric Gastroenterology": HealthcareSpecialities.PAEDIATRICS,
            "Paediatrics": HealthcareSpecialities.PAEDIATRICS,
            "Paediatric Surgery": HealthcareSpecialities.PAEDIATRIC_SURGERY,
            "Pain Medicine": HealthcareSpecialities.PAIN_MEDICINE,
            "Palliative Care": HealthcareSpecialities.PALLIATIVE,
            "Pathology": HealthcareSpecialities.PATHOLOGY,
            "Plastic and Reconstructive Surgery - Hand Surgery": HealthcareSpecialities.PLASTIC_SURGERY,
            "Plastic and Reconstructive Surgery": HealthcareSpecialities.PLASTIC_SURGERY,
            "Podiatry": HealthcareSpecialities.PODIATRY,
            "Psychiatry - Addictions": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Adult ADHD": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Adult (General)": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Aged Psychiatry": HealthcareSpecialities.PHYSIATRY,
            "Psychiatry - Anxiety Disorders": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Child and Adolescent": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Consultation Liaison Psychiatry": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Dementia": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Dissociative Disorder": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Family/Couple Therapy": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - GP Management Plans Item 291": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry": HealthcareSpecialities.PHYSIATRY,
            "Psychiatry - Medico Legal Reports": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Mood Disorders": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Pain Management": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Parent and Infant": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Perinatal": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Personality Disorders": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Psychosis": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Psychotherapy": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Second Opinions": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Sexuality and Gender Incongruence": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Trauma/PTSD": HealthcareSpecialities.PSYCHIATRY,
            "Psychiatry - Workcover/TAC": HealthcareSpecialities.PSYCHIATRY,
            "Psychology": None,
            "Radiation Oncology": HealthcareSpecialities.RADIOTHERAPY,
            "Rehabilitation": HealthcareSpecialities.REHABILITATION,
            "Renal Medicine": HealthcareSpecialities.NEPHROLOGY,
            "Respiratory and Sleep Medicine": HealthcareSpecialities.SLEEP_MEDICINE,
            "Respiratory": HealthcareSpecialities.PULMONOLOGY,
            "Rheumatology": HealthcareSpecialities.RHEUMATOLOGY,
            "Robotic Surgery": HealthcareSpecialities.SURGERY,
            "Speech Pathology": None,
            "Spine Surgery": HealthcareSpecialities.SURGERY,
            "Sports Medicine": HealthcareSpecialities.PHYSIATRY,
            "Surgical Oncology": HealthcareSpecialities.ONCOLOGY,
            "Thoracic Surgery": HealthcareSpecialities.CARDIOTHORACIC_SURGERY,
            "Upper Gastro Intestinal Surgery": HealthcareSpecialities.GASTROENTEROLOGY,
            "Urogynaecology": HealthcareSpecialities.GYNAECOLOGY,
            "Urology": HealthcareSpecialities.UROLOGY,
            "Vascular Surgery": HealthcareSpecialities.VASCULAR_SURGERY,
        }
        listed_specialities = set(map(str.strip, feature.get("Specialties", "").split(",")))
        known_specialities = set(specialities_mapping.keys())

        matched_specialities_keys = listed_specialities | known_specialities
        matched_specialities = [
            v for k, v in specialities_mapping.items() if v is not None and k in matched_specialities_keys
        ]
        apply_healthcare_specialities(matched_specialities, item)
        if HealthcareSpecialities.EMERGENCY in matched_specialities:
            item["extras"]["emergency"] = "yes"
        else:
            item["extras"]["emergency"] = "no"

        unmatched_specialities_keys = listed_specialities - known_specialities
        for unmatched_speciality_key in list(filter(None, unmatched_specialities_keys)):
            self.logger.warning(
                "Hospital has additional unknown and ignored healthcare speciality of: {}".format(
                    unmatched_speciality_key
                )
            )

        yield item
