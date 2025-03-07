from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.settings import ITEM_PIPELINES
from locations.storefinders.yext_answers import YextAnswersSpider

CATEGORY_MAP = {
    "Birth Center": Categories.BIRTHING_CENTRE,
    "Care Center": Categories.DOCTOR_GP,
    "Emergency Room": Categories.EMERGENCY_WARD,
    "Hospital": Categories.HOSPITAL,
    "Imaging": Categories.CLINIC,
    "Integrative Health and Healing": Categories.ALTERNATIVE_MEDICINE,
    "Lab": Categories.MEDICAL_LABORATORY,
    "Pharmacy (Outpatient)": Categories.PHARMACY,
    "Physical Therapy and Rehab": Categories.PHYSIOTHERAPIST,
    "Surgery Center": Categories.CLINIC,
    "Transplant Outreach Clinic": Categories.CLINIC,
    "Urgent Care": Categories.CLINIC_URGENT,
    "Walk-In Care": Categories.CLINIC,
}

CATEGORY_SPECIALTY_MAP = {
    "Emergency Room": HealthcareSpecialities.EMERGENCY,
    "Imaging": HealthcareSpecialities.RADIOLOGY,
    "Surgery Center": HealthcareSpecialities.SURGERY,
    "Transplant Outreach Clinic": HealthcareSpecialities.TRANSPLANT,
}


class SutterHealthUSSpider(YextAnswersSpider):
    name = "sutter_health_us"
    item_attributes = {"brand": "Sutter Health", "brand_wikidata": "Q7650154"}
    custom_settings = {  # NSI currently only has surgery centers
        "ITEM_PIPELINES": ITEM_PIPELINES | {"locations.pipelines.apply_nsi_categories.ApplyNSICategoriesPipeline": None}
    }
    endpoint = "https://prod-cdn.us.yextapis.com/v2/accounts/me/search/vertical/query"
    api_key = "759b3268344d034ed4f81ed0593e4bbb"
    experience_key = "search"
    feature_type = "healthcare_facilities"

    def parse_item(self, location, item):
        item["branch"] = item.pop("name")
        item["ref"] = item["ref"].removeprefix("location-")
        item["operator"] = ";".join(affiliate["name"] for affiliate in location.get("c_affiliate", []))

        if "c_image" in location:
            item["image"] = location["c_image"]["url"]

        if "slug" in location and "uid" in location:
            item["website"] = (
                f"https://www.sutterhealth.org/find-location/facility/{location['slug']}-{location['uid']}"
            )

        for location_type in location.get("c_locationType", []):
            if location_type in CATEGORY_MAP:
                apply_category(CATEGORY_MAP[location_type], item)
                if location_type in CATEGORY_SPECIALTY_MAP:
                    apply_healthcare_specialities([CATEGORY_SPECIALTY_MAP[location_type]], item)
            else:
                apply_category(Categories.CLINIC, item)
                item["extras"]["object_type"] = location_type
                self.crawler.stats.inc_value(f"atp/sutter_health/unmapped_category/{location_type}")

        yield item
