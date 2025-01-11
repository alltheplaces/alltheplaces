import json

from scrapy import Request
from scrapy.spiders import SitemapSpider
from scrapy.utils.sitemap import sitemap_urls_from_robots

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider, extract_email, extract_phone

CATEGORY_MAP = {
    "Behavioral Health Facility": Categories.PSYCHOTHERAPIST,
    "Dental Services": Categories.DENTIST,
    "Dental Office": Categories.DENTIST,
    "Dialysis Center": Categories.DIALYSIS,
    "Durable Medical Equipment Supplier": Categories.SHOP_MEDICAL_SUPPLY,
    "Emergency Care Center": Categories.EMERGENCY_WARD,
    "Hospital": Categories.HOSPITAL,
    "Medical Office Building": Categories.DOCTOR_GP,
    "Other": Categories.CLINIC,
    "Outpatient Surgery Center": Categories.CLINIC,
    "Pharmacy": Categories.PHARMACY,
    "Plan Hospital": Categories.HOSPITAL,
    "Rehabilitation Facility": Categories.REHABILITATION,
    "Skilled Nursing Facility": Categories.NURSING_HOME,
    "Urgent Care Center": Categories.CLINIC_URGENT,
    "Vision Care": Categories.OPTOMETRIST,
}

CATEGORY_SPECIALTY_MAP = {
    "Behavioral Health Facility": HealthcareSpecialities.PSYCHOTHERAPHY_BEHAVIOR,
    "Emergency Care Center": HealthcareSpecialities.EMERGENCY,
    "Outpatient Surgery Center": HealthcareSpecialities.SURGERY,
    "Rehabilitation Facility": HealthcareSpecialities.REHABILITATION,
}

DEPARTMENT_TYPE_MAP = {
    "Addiction Medicine": HealthcareSpecialities.GENERAL,
    "Allergy": HealthcareSpecialities.ALLERGOLOGY,
    "Audiology": None,
    "Cardiac Catheterization Laboratory": None,
    "Cardiac Surgery": HealthcareSpecialities.CARDIOTHORACIC_SURGERY,
    "Cardiology": HealthcareSpecialities.CARDIOLOGY,
    "Dermatology": HealthcareSpecialities.DERMATOLOGY,
    "Diagnostic Imaging/Radiology": HealthcareSpecialities.RADIOLOGY,
    "Dialysis Unit": None,
    "Emergency Department": HealthcareSpecialities.EMERGENCY,
    "Endocrinology/Diabetes": HealthcareSpecialities.ENDOCRINOLOGY,
    "Eye Care Services": HealthcareSpecialities.OPHTHALMOLOGY,
    "Family Practice": HealthcareSpecialities.GENERAL,
    "Farmer's Market": None,
    "Flu Injection Clinic": None,
    "Food and Nutrition": None,
    "Gastroenterology": HealthcareSpecialities.GASTROENTEROLOGY,
    "Gastroenterology/Hepatology": HealthcareSpecialities.HEPATOLOGY,
    "General": HealthcareSpecialities.GENERAL,
    "Genetics": None,
    "Gift Shop": None,
    "Gynecologic Oncology": HealthcareSpecialities.GYNAECOLOGY,
    "Head and Neck Surgery": None,  # "otolaryngology",
    "Health Education Center": None,
    "Health Education": None,
    "Hearing": None,
    "Home Health": None,
    "Hospice Home Care": HealthcareSpecialities.PALLIATIVE,
    "Infectious Disease": HealthcareSpecialities.INFECTIOUS_DISEASES,
    "Injection Clinics": None,
    "Insurance": None,
    "Internal Medicine": HealthcareSpecialities.INTERNAL,
    "Laboratory": None,
    "Language services": None,
    "Long-term Care": None,
    "Medical correspondence": None,
    "Member services": None,
    "Neurology": HealthcareSpecialities.NEUROLOGY,
    "Neurosurgery": HealthcareSpecialities.NEUROSURGERY,
    "Nuclear Medicine": HealthcareSpecialities.NUCLEAR,
    "Obstetrics/Gynecology": HealthcareSpecialities.GYNAECOLOGY,
    "Occupational Health": HealthcareSpecialities.OCCUPATIONAL,
    "Ophthalmology": HealthcareSpecialities.OPHTHALMOLOGY,
    "Optometry": None,
    "Orthopedics/Podiatry": HealthcareSpecialities.PODIATRY,
    "Other Administrative Services": None,
    "Other Clinical Services": None,
    "Outpatient Infusion Center": None,
    "Pain Management Center": None,
    "Pediatrics/Teenage Medicine": HealthcareSpecialities.PAEDIATRICS,
    "Pharmacy": None,
    "Physical Medicine and Rehabilitation": HealthcareSpecialities.PHYSIATRY,
    "Physical, Occupational, Speech Therapy": None,
    "Psychiatry": HealthcareSpecialities.PSYCHIATRY,
    "Pulmonary Function Laboratory": HealthcareSpecialities.PULMONOLOGY,
    "Pulmonary Rehabilitation": HealthcareSpecialities.PULMONOLOGY,
    "Radiation Oncology": HealthcareSpecialities.ONCOLOGY,
    "Radiology": HealthcareSpecialities.RADIOLOGY,
    "Social Medicine": HealthcareSpecialities.COMMUNITY,
    "Surgery": HealthcareSpecialities.SURGERY,
    "Travel Services": None,
    "Urgent/After-hours Care": None,
    "Urgent Care": None,
    "Urology": HealthcareSpecialities.UROLOGY,
    "Vision Essentials": HealthcareSpecialities.OPHTHALMOLOGY,
    "Volunteer Services": None,
}


class KaiserPermanenteUSSpider(SitemapSpider, StructuredDataSpider):
    name = "kaiser_permanente_us"
    allowed_domains = ["healthy.kaiserpermanente.org"]
    sitemap_urls = ["https://healthy.kaiserpermanente.org/robots.txt"]
    sitemap_follow = ["/facilities/"]
    wanted_types = ["MedicalBusiness"]
    custom_settings = {
        # The KP website likes to set cookies and then redirect to the same page, which Scrapy counts as a duplicate request.
        "DUPEFILTER_CLASS": "scrapy.dupefilters.BaseDupeFilter",
    }
    search_for_facebook = False
    search_for_twitter = False

    def _parse_sitemap(self, response):
        # SitemapSpider doesn't honour sitemap_follow while parsing robots.txt
        if response.url.endswith("/robots.txt"):
            for url in sitemap_urls_from_robots(response.text, base_url=response.url):
                if "/facilities/" in url:
                    yield Request(url, callback=self._parse_sitemap)
        else:
            yield from super()._parse_sitemap(response)

    def parse(self, response):
        # First try structured data
        sd_results = list(self.parse_sd(response))
        if len(sd_results) > 0:
            yield from sd_results
            return

        # Next, try this JSON
        facility_directions = response.xpath("//script[@class='js-facility-directions']/text()").get()
        if len(facility_directions.strip()) > 0:
            item = DictParser.parse(json.loads(facility_directions))
            item["street_address"] = item.pop("street", None)
            item["website"] = response.url

        # Finally, HTML
        else:
            item = Feature(name=response.xpath("//@data-name"))

        extract_email(item, response)
        extract_phone(item, response)
        yield from self.post_process_item(item, response, {})

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["lat"] = response.xpath("//@data-lat").get()
        item["lon"] = response.xpath("//@data-lng").get()
        item["ref"] = response.xpath("//@data-id").get()
        item["image"] = ld_data.get("photo")
        if item["phone"] == "+1-866-454-8855":
            del item["phone"]

        # "Affiliated" locations are not KP-branded
        if response.xpath("//@data-affiliated").get() != "true":
            apply_category({"brand": "Kaiser Permanente", "brand:wikidata": "Q1721601"}, item)

        cat = response.xpath("//@data-type").get()
        if cat in CATEGORY_MAP:
            apply_category(CATEGORY_MAP[cat], item)
            if cat in CATEGORY_SPECIALTY_MAP:
                apply_healthcare_specialities([CATEGORY_SPECIALTY_MAP[cat]], item)
        else:
            apply_category(Categories.CLINIC, item)
            item["extras"]["type"] = cat
            self.crawler.stats.inc_value(f"atp/kaiser_permanente_us/unmapped_category/{cat}")

        if "department" in ld_data:
            specialities = [
                DEPARTMENT_TYPE_MAP.get(department["medicalSpecialty"]) for department in ld_data["department"]
            ]
            apply_healthcare_specialities(filter(None, specialities), item)

            for department in ld_data["department"]:
                specialty = department["medicalSpecialty"]
                if specialty not in DEPARTMENT_TYPE_MAP:
                    self.crawler.stats.inc_value(f"atp/kaiser_permanente_us/unmapped_specialty/{specialty}")

        yield item
