from scrapy.http import JsonRequest

from locations.camoufox_spider import CamoufoxSpider
from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE


class NorthsideHospitalUSSpider(CamoufoxSpider):
    name = "northside_hospital_us"
    item_attributes = {"brand": "Northside Hospital", "brand_wikidata": "Q7059745"}
    start_urls = ["https://locations-api-prod.northside.com/api/LocationsSearch?&Page=1&PageSize=10"]
    captcha_type = "cloudflare_turnstile"
    captcha_selector_indicating_success = '//link[@href="resource://content-accessible/plaintext.css"]'
    custom_settings = DEFAULT_CAMOUFOX_SETTINGS_FOR_CLOUDFLARE_TURNSTILE
    handle_httpstatus_list = [403]

    _category_map = {
        "Cancer Services": (Categories.HOSPITAL, [HealthcareSpecialities.ONCOLOGY]),
        "Colorectal Surgery": (Categories.HOSPITAL, [HealthcareSpecialities.PROCTOLOGY]),
        "Hospital": (Categories.HOSPITAL, []),
        "Imaging Center": (Categories.MEDICAL_IMAGING, [HealthcareSpecialities.DIAGNOSTIC_RADIOLOGY]),
        "Outpatient": (Categories.CLINIC, []),
        "Primary Care": (Categories.DOCTOR_GP, []),
        "Radiation Therapy": (Categories.HOSPITAL, [HealthcareSpecialities.NUCLEAR]),
        "Rehabilitation Services": (Categories.CLINIC, [HealthcareSpecialities.REHABILITATION]),
        "Specialty Care": (Categories.CLINIC, []),
        "Spine and Pain Management": (
            Categories.CLINIC,
            [HealthcareSpecialities.CHIROPRATIC, HealthcareSpecialities.PAIN_MEDICINE],
        ),
        "Surgery Center": (Categories.HOSPITAL, [HealthcareSpecialities.SURGERY]),
        "Urgent Care": (Categories.CLINIC_URGENT, []),
        "Vascular Surgery": (Categories.HOSPITAL, [HealthcareSpecialities.VASCULAR_SURGERY]),
    }

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            location["street_address"] = merge_address_lines([location.pop("address"), location.pop("addressLine2")])
            item = DictParser.parse(location)
            item["ref"] = location["id_string"]
            item["state"] = location["state"]["abbreviation"]
            item["image"] = location["image_url"]
            item["phone"] = location["phone_1"]
            item["website"] = location["listing_url"]

            if cat := self._category_map.get(location["category"]):
                apply_category(cat[0], item)
                apply_healthcare_specialities(cat[1], item)
            else:
                self.logger.warning("Unknown category: {}".format(location["category"]))
                apply_category(Categories.CLINIC, item)

            yield item

        if next_page := response.json()["nextPageUrl"]:
            yield JsonRequest(next_page.replace("pageNumber", "page"))
