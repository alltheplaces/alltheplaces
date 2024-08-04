from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.settings import ITEM_PIPELINES
from locations.structured_data_spider import StructuredDataSpider

CATEGORY_MAP = {
    "birth-centers": Categories.BIRTHING_CENTRE,
    "care-centers": Categories.DOCTOR_GP,
    "emergency-rooms": Categories.EMERGENCY_WARD,
    "home-health-hospice": Categories.HOSPICE,
    "hospitals": Categories.HOSPITAL,
    "imaging": Categories.CLINIC,
    "integrative-health-healing": Categories.ALTERNATIVE_MEDICINE,
    "labs": Categories.MEDICAL_LABORATORY,
    "libraries-resource-centers": {"amenity": "library", "operator:type": "private"},
    "occupational-health": {"healthcare": "occupational_therapist"},
    "pharmacies-outpatient": Categories.PHARMACY,
    "physical-therapy-rehab": Categories.PHYSIOTHERAPIST,
    "surgery-centers": Categories.CLINIC,
    "transplant-outreach-clinics": Categories.CLINIC,
    "urgent-care": Categories.CLINIC_URGENT,
    "walk-in-care": Categories.CLINIC,
}

CATEGORY_SPECIALTY_MAP = {
    "emergency-rooms": HealthcareSpecialities.EMERGENCY,
    "imaging": HealthcareSpecialities.RADIOLOGY,
    "occupational-health": HealthcareSpecialities.OCCUPATIONAL,
    "surgery-centers": HealthcareSpecialities.SURGERY,
    "transplant-outreach-clinics": HealthcareSpecialities.TRANSPLANT,
}

SERVICES_MAP = {
    "Allergy Care": HealthcareSpecialities.ALLERGOLOGY,
    "Alzheimer's and Brain Health": None,
    "Arthritis and Rheumatology": HealthcareSpecialities.RHEUMATOLOGY,
    "Asthma Care": HealthcareSpecialities.ALLERGOLOGY,
    "Back and Spine Services": None,
    "Behavioral Health Care": HealthcareSpecialities.PSYCHOTHERAPHY_BEHAVIOR,
    "Bioethics Services": None,
    "Cancer Services": HealthcareSpecialities.ONCOLOGY,
    "Cosmetic Surgery": HealthcareSpecialities.PLASTIC_SURGERY,
    "Dermatology Services": HealthcareSpecialities.DERMATOLOGY,
    "Diabetes Services": HealthcareSpecialities.ENDOCRINOLOGY,
    "Ear, Nose and Throat Services": HealthcareSpecialities.OTOLARYNGOLOGY,
    "Emergency Services": HealthcareSpecialities.EMERGENCY,
    "Endocrinology": HealthcareSpecialities.ENDOCRINOLOGY,
    "Fertility Services": HealthcareSpecialities.FERTILITY,
    "Gastroenterology": HealthcareSpecialities.GASTROENTEROLOGY,
    "Gynecology and Women's Health": HealthcareSpecialities.GYNAECOLOGY,
    "Health Education": None,
    "Heart and Vascular Services": None,
    "Holistic and Integrative Medicine": None,
    "Home Health and Hospice Care": HealthcareSpecialities.PALLIATIVE,
    "Imaging": HealthcareSpecialities.RADIOLOGY,
    "Kidney Disease and Nephrology": HealthcareSpecialities.NEPHROLOGY,
    "LGBTQI+ Care": None,
    "Lab and Pathology": HealthcareSpecialities.PATHOLOGY,
    "Liver Care": HealthcareSpecialities.HEPATOLOGY,
    "Neuroscience": HealthcareSpecialities.NEUROLOGY,
    "Nutrition Services": None,
    "Occupational Health": HealthcareSpecialities.OCCUPATIONAL,
    "Orthopedic Services": HealthcareSpecialities.ORTHOPAEDICS,
    "Palliative Care and Advanced Illness Management": HealthcareSpecialities.PALLIATIVE,
    "Pediatric Services": HealthcareSpecialities.PAEDIATRICS,
    "Physical Therapy and Rehabilitation": HealthcareSpecialities.PHYSIATRY,
    "Podiatric Services": HealthcareSpecialities.PODIATRY,
    "Pregnancy and Childbirth Services": None,
    "Primary Care": HealthcareSpecialities.GENERAL,
    "Pulmonary Care": HealthcareSpecialities.PULMONOLOGY,
    "Reconstructive Plastic Surgery": HealthcareSpecialities.PLASTIC_SURGERY,
    "Senior Services and Geriatric Care": HealthcareSpecialities.GERIATRICS,
    "Surgical Services": HealthcareSpecialities.SURGERY,
    "Transplant Services": HealthcareSpecialities.TRANSPLANT,
    "Urgent Care": None,  # HealthcareSpecialities.URGENT,
    "Urology": HealthcareSpecialities.UROLOGY,
    "Vision Care": HealthcareSpecialities.OPHTHALMOLOGY,
    "Weight Loss Services": None,
}


class SutterHealthUSSpider(CrawlSpider, StructuredDataSpider):
    name = "sutter_health_us"
    item_attributes = {"brand": "Sutter Health", "brand_wikidata": "Q7650154"}
    allowed_domains = ["sutterhealth.org", "www.sutterhealth.org"]
    start_urls = ["https://www.sutterhealth.org/location-search?start=1&max=50"]
    wanted_types = ["MedicalClinic"]
    custom_settings = {  # NSI currently only has surgery centers
        "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None}
    }
    rules = [
        Rule(
            LinkExtractor(allow=r"^https:\/\/www\.sutterhealth\.org\/find-location\/facility\/[a-z-]+"),
            callback="parse_sd",
            follow=False,
        ),
    ]

    def process_results(self, response, results):
        yield from results
        url = urlparse(response.url)
        if url.path == "/location-search":
            count = int(response.xpath("//@data-total").get())
            query = dict(parse_qsl(url.query))
            start = int(query.get("start", 1)) + int(query.get("max", 50))
            if start <= count:
                query["start"] = str(start)
                next_url = urlunparse(url._replace(query=urlencode(query)))
                yield response.follow(next_url)

    def pre_process_data(self, item):
        opening_hours = item.get("openinghours", item.get("opens"))
        if opening_hours is not None and not isinstance(opening_hours, list):
            opening_hours = [opening_hours]
        item["openingHours"] = opening_hours

    def post_process_item(self, item, response, ld_data):
        cat = response.xpath('//*[@id="location-type"]/@value').get()
        if cat in CATEGORY_MAP:
            apply_category(CATEGORY_MAP[cat], item)
            if cat in CATEGORY_SPECIALTY_MAP:
                apply_healthcare_specialities([CATEGORY_SPECIALTY_MAP[cat]], item)
        else:
            apply_category(Categories.CLINIC, item)
            item["extras"]["type"] = cat
            self.crawler.stats.inc_value(f"atp/sutter_health/unmapped_category/{cat}")

        specialties = [
            SERVICES_MAP.get(node.get()) for node in response.xpath('//*[contains(@class, "s-top")]//a/text()')
        ]
        apply_healthcare_specialities([s for s in specialties if s is not None], item)

        yield item
