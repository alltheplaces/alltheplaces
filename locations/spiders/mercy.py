import json

import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class MercySpider(scrapy.Spider):
    name = "mercy"
    item_attributes = {"brand": "Mercy", "brand_wikidata": "Q30289045"}
    allowed_domains = ["mercy.net"]
    start_urls = [
        "https://www.mercy.net/content/mercy/us/en.solrQueryhandler?q=*:*&solrsort=&latitude=38.627002&longitude=-90.199404&start=0&rows=10&locationType=&locationOfferings=&servicesOffered=&distance=9999&noResultsSuggestions=true&pagePath=%2Fsearch%2Flocation"
    ]

    categories = [
        ("Doctor's Office", Categories.DOCTOR_GP),
        ("Hospital or Emergency Room", Categories.HOSPITAL),
        ("Pharmacy", Categories.PHARMACY),
        ("Imaging, Labs or Tests", {"healthcare": "laboratory"}),
        ("Rehabilitation, Sports Medicine or Fitness", {"healthcare": "physiotherapist"}),
        ("Behavioral Health", {"healthcare": "counselling"}),
        ("Childbirth", {"healthcare": "midwife"}),
        ("Vaccinations", {"healthcare": "vaccination_centre"}),
        ("Urgent Care or Convenient Care", Categories.CLINIC_URGENT),
        ("Surgery", {"amenity": "hospital", "healthcare": "hospital", "healthcare:speciality": "surgery"}),
        ("Mission and Ministry", {"amenity": "social_centre"}),
        ("Cancer Treatment Center", {"healthcare": "centre", "healthcare:speciality": "cancer_treatment_centre"}),
        ("Hearing and Vision", {"healthcare": "centre", "healthcare:speciality": "optometrist;audiologist"}),
        ("Infusion", Categories.CLINIC),
        ("Mercy Kids", Categories.HOSPITAL),
        ("Women's Health", {"healthcare": "centre"}),
        ("Community and Corporate Health", {"amenity": "social_centre"}),
        ("Education", {"healthcare": "centre"}),
        ("Gastroenterology Center", {"healthcare": "centre", "healthcare:speciality": "gastroenterology"}),
        ("Home Health and Hospice", Categories.HOSPICE),
        ("Multispecialty Care", {"healthcare": "centre"}),
        ("Retail", Categories.SHOP_GIFT),
        ("Skilled Nursing", {"healthcare": "nurse"}),
    ]

    def parse(self, response):
        number_locations = response.json().get("numFound")
        url = f"https://www.mercy.net/content/mercy/us/en.solrQueryhandler?q=*:*&solrsort=&latitude=38.627002&longitude=-90.199404&start=0&rows={number_locations}&locationType=&locationOfferings=&servicesOffered=&distance=9999&noResultsSuggestions=true&pagePath=/search/location"
        yield scrapy.Request(url=url, callback=self.parse_location)

    def parse_location(self, response):
        for data in response.json().get("docs"):
            item = DictParser.parse(data)
            item["lat"] = data.get("location_0_coordinate")
            item["lon"] = data.get("location_1_coordinate")
            item["name"] = data.get("jcr_title")
            item["street_address"] = item.pop("addr_full")
            item["website"] = f'https://www.{self.allowed_domains[0]}{data.get("url")}'
            item["ref"] = f'https://www.{self.allowed_domains[0]}{data.get("id")}'

            oh = OpeningHours()
            if data.get("operationHours"):
                for day, value in json.loads(data.get("operationHours")[0]).items():
                    if value.get("status") == "Closed":
                        continue
                    for helfday in value.get("hours"):
                        oh.add_range(
                            day=day,
                            open_time=helfday.get("start"),
                            close_time=helfday.get("end"),
                        )

            item["opening_hours"] = oh

            if not data.get("marketSiteOfServiceType"):
                apply_category({"healthcare": "centre"}, item)
            else:
                for label, cat in self.categories:
                    if label in data["marketSiteOfServiceType"]:
                        apply_category(cat, item)
                        break
                else:
                    for cat in data["marketSiteOfServiceType"]:
                        self.crawler.stats.inc_value(f"atp/mercy/unmatched_category/{cat}")

            yield item
