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
    "/anticoagulation-clinics/": [Categories.CLINIC],
    "/audiology-hearing/": [Categories.AUDIOLOGIST],
    "/bariatrics-weight-management/": [Categories.CLINIC, HealthcareSpecialities.BARIATRIC_SURGERY],
    "/behavioral-mental-health/": [Categories.PSYCHOTHERAPIST, HealthcareSpecialities.PSYCHOTHERAPHY_BEHAVIOR],
    "/breast-health/": [Categories.CLINIC, HealthcareSpecialities.ONCOLOGY],
    "/cancer-care-oncology/": [Categories.CLINIC, HealthcareSpecialities.ONCOLOGY],
    "/dermatology/": [Categories.CLINIC, HealthcareSpecialities.DERMATOLOGY],
    "/endocrinology-diabetes/": [Categories.CLINIC, HealthcareSpecialities.ENDOCRINOLOGY],
    "/ent-ear-nose-throat/": [Categories.CLINIC, HealthcareSpecialities.OTOLARYNGOLOGY],
    "/emergency-room/": [Categories.EMERGENCY_WARD],
    "/fitness-healthplex/": [Categories.GYM],
    "/general-surgery/": [Categories.CLINIC, HealthcareSpecialities.SURGERY],
    "/geriatrics-senior-care/": [Categories.CLINIC, HealthcareSpecialities.GERIATRICS],
    "/gi-liver-pancreas/": [Categories.CLINIC, HealthcareSpecialities.GASTROENTEROLOGY],
    "/gynecology-obgyn-womens-health/": [Categories.CLINIC, HealthcareSpecialities.GYNAECOLOGY],
    "/heart-care-vascular-care/": [Categories.CLINIC, HealthcareSpecialities.CARDIOLOGY],
    "/home-health-care/": [Categories.CLINIC],
    "/hospice-care-palliative-care/": [Categories.HOSPICE],
    "/hospitals/": [Categories.HOSPITAL],
    "/infectious-disease-specialists/": [Categories.CLINIC, HealthcareSpecialities.INFECTIOUS_DISEASES],
    "/lab-and-imaging-centers/": [Categories.MEDICAL_LABORATORY],
    "/maternity-care-birthing-centers/": [Categories.BIRTHING_CENTRE],
    "/medical-centers-clinics/": [Categories.CLINIC],
    "/nephrology-kidney-care/": [Categories.CLINIC, HealthcareSpecialities.NEPHROLOGY],
    "/neurology-neurosurgery-neuroscience/": [
        Categories.CLINIC,
        HealthcareSpecialities.NEUROLOGY,
        HealthcareSpecialities.NEUROSURGERY,
    ],
    "/occupational-health/": [Categories.CLINIC, HealthcareSpecialities.OCCUPATIONAL],
    "/orthopedics-sports-medicine-spine/": [Categories.CLINIC, HealthcareSpecialities.ORTHOPAEDICS],
    "/other-locations/": [Categories.CLINIC],
    "/pain-management/": [Categories.CLINIC, HealthcareSpecialities.PAIN_MEDICINE],
    "/pediatrics/": [Categories.CLINIC, HealthcareSpecialities.PAEDIATRICS],
    "/pharmacy/": [Categories.PHARMACY],
    "/physical-therapy-rehabilitation/": [Categories.REHABILITATION, HealthcareSpecialities.REHABILITATION],
    "/podiatry-foot-care/": [Categories.CLINIC, HealthcareSpecialities.PODIATRY],
    "/primary-care-family-medicine/": [Categories.DOCTOR_GP],
    "/pulmonary-respiratory-care/": [Categories.CLINIC, HealthcareSpecialities.PULMONOLOGY],
    "/reconstructive-plastic-surgery/": [Categories.CLINIC, HealthcareSpecialities.PLASTIC_SURGERY],
    "/rheumatology/": [Categories.CLINIC, HealthcareSpecialities.RHEUMATOLOGY],
    "/school-based-health-clinics/": [Categories.CLINIC],
    "/senior-living/": [Categories.NURSING_HOME],
    "/sleep-medicine-sleep-centers/": [Categories.CLINIC, HealthcareSpecialities.SLEEP_MEDICINE],
    "/urgent-care/": [Categories.CLINIC_URGENT],
    "/urology-pelvic-floor/": [Categories.CLINIC, HealthcareSpecialities.UROLOGY],
    "/vein-therapy/": [Categories.CLINIC, HealthcareSpecialities.VASCULAR_SURGERY],
    "/walk-in-care-clinics/": [Categories.CLINIC_URGENT],
    "/wound-care/": [Categories.CLINIC, HealthcareSpecialities.WOUND_TREATMENT],
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
            for url_slug in HEALTHCARE_CATEGORIES.keys():
                if url_slug in item["website"]:
                    for tags in HEALTHCARE_CATEGORIES[url_slug]:
                        if isinstance(tags, Categories):
                            apply_category(tags, item)
                        elif isinstance(tags, HealthcareSpecialities):
                            apply_healthcare_specialities([tags], item)
                    if "/.home-health-care/" in item["website"]:
                        apply_yes_no("home_visit", item, True)
                    break
            yield item
