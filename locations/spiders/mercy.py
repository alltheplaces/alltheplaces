from json import loads
from typing import Iterable

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class MercySpider(Spider):
    name = "mercy"
    item_attributes = {"brand": "Mercy", "brand_wikidata": "Q30289045"}
    allowed_domains = ["mercy.net"]
    start_urls = [
        "https://www.mercy.net/content/mercy/us/en.solrQueryhandler?q=*:*&solrsort=&latitude=38.627002&longitude=-90.199404&start=0&rows=10&locationType=&locationOfferings=&servicesOffered=&distance=9999&noResultsSuggestions=true&pagePath=%2Fsearch%2Flocation"
    ]

    categories = {
        "Doctor's Office": (Categories.DOCTOR_GP, []),
        "Hospital or Emergency Room": (Categories.HOSPITAL, []),
        "Pharmacy": (Categories.PHARMACY, []),
        "Imaging, Labs or Tests": (Categories.MEDICAL_IMAGING, [HealthcareSpecialities.DIAGNOSTIC_RADIOLOGY]),
        "Rehabilitation, Sports Medicine or Fitness": (Categories.PHYSIOTHERAPIST, []),
        "Behavioral Health": (Categories.PSYCHOTHERAPIST, [HealthcareSpecialities.PSYCHOTHERAPHY_BEHAVIOR]),
        "Childbirth": (Categories.BIRTHING_CENTRE, []),
        "Vaccinations": (Categories.VACCINATION_CENTRE, []),
        "Urgent Care or Convenient Care": (Categories.CLINIC_URGENT, []),
        "Surgery": (Categories.HOSPITAL, [HealthcareSpecialities.SURGERY]),
        "Mission and Ministry": (Categories.SOCIAL_CENTRE, []),
        "Cancer Treatment Center": (Categories.CLINIC, [HealthcareSpecialities.ONCOLOGY]),
        "Hearing and Vision": (Categories.CLINIC, [HealthcareSpecialities.OPHTHALMOLOGY, HealthcareSpecialities.OTOLARYNGOLOGY]),
        "Infusion": (Categories.CLINIC, []),
        "Mercy Kids": (Categories.HOSPITAL, [HealthcareSpecialities.PAEDIATRICS]),
        "Women's Health": (Categories.CLINIC, [HealthcareSpecialities.GYNAECOLOGY]),
        "Community and Corporate Health": (Categories.SOCIAL_CENTRE, []),
        "Education": (Categories.CLINIC, []),
        "Gastroenterology Center": (Categories.CLINIC, [HealthcareSpecialities.GASTROENTEROLOGY]),
        "Home Health and Hospice": (Categories.HOSPICE, []),
        "Multispecialty Care": (Categories.CLINIC, []),
        "Retail": (Categories.SHOP_GIFT, []),
        "Skilled Nursing": (Categories.NURSE_CLINIC, []),
    }

    def parse(self, response: Response) -> Iterable[Request]:
        number_locations = response.json().get("numFound")
        url = f"https://www.mercy.net/content/mercy/us/en.solrQueryhandler?q=*:*&solrsort=&latitude=38.627002&longitude=-90.199404&start=0&rows={number_locations}&locationType=&locationOfferings=&servicesOffered=&distance=9999&noResultsSuggestions=true&pagePath=/search/location"
        yield Request(url=url, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        for data in response.json().get("docs"):
            item = DictParser.parse(data)
            item["lat"] = data.get("location_0_coordinate")
            item["lon"] = data.get("location_1_coordinate")
            item["name"] = data.get("jcr_title")
            item["street_address"] = item.pop("addr_full")
            item["website"] = f'https://www.{self.allowed_domains[0]}{data.get("url")}'
            item["ref"] = f'https://www.{self.allowed_domains[0]}{data.get("id")}'

            item["opening_hours"] = OpeningHours()
            if data.get("operationHours"):
                for day, value in loads(data.get("operationHours")[0]).items():
                    if value.get("status") == "Closed":
                        continue
                    for halfday in value.get("hours"):
                        item["opening_hours"].add_range(
                            day=day,
                            open_time=halfday.get("start"),
                            close_time=halfday.get("end"),
                        )

            if not data.get("marketSiteOfServiceType"):
                apply_category(Categories.CLINIC, item)
            else:
                feature_type_match = False
                for feature_type in self.categories.keys():
                    if feature_type in data["marketSiteOfServiceType"]:
                        apply_category(self.categories[feature_type][0], item)
                        apply_healthcare_specialities(self.categories[feature_type][1], item)
                        feature_type_match = True
                        break
                if not feature_type_match:
                    for cat in data["marketSiteOfServiceType"]:
                        self.logger.warning("Unknown feature type: {}".format(cat))
                        self.crawler.stats.inc_value(f"atp/mercy/unmatched_category/{cat}")

            yield item
