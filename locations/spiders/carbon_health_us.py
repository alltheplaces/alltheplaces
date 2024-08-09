import json

from scrapy import Request, Spider

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class CarbonHealthUSSpider(Spider):
    name = "carbon_health_us"
    item_attributes = {"brand": "Carbon Health", "brand_wikidata": "Q110076263"}

    def start_requests(self):
        yield Request("https://carbonhealth.com/locations", headers={"RSC": "1"})

    def parse(self, response):
        data = None
        for line in response.body.splitlines():
            line = line[line.find(b":") + 1 :].strip()
            if line[0] != ord("["):
                continue
            components = json.loads(line)
            for component in components:
                if isinstance(component, dict) and "locations" in component:
                    data = component
                    break
            if data is not None:
                break
        if data is None:
            raise Exception("Can't find data")

        specialty_id_to_speciality = {}
        urgent_care_specialty_ids = set()
        for specialty in data["allSpecialties"]:
            code = specialty["taxonomyCode"]
            if code == "207R00000X":
                specialty_id_to_speciality[specialty["id"]] = HealthcareSpecialities.INTERNAL
            elif code == "261QU0200X":
                urgent_care_specialty_ids.add(specialty["id"])

        for location in data["locations"]:
            item = DictParser.parse(location)
            item["branch"] = item["name"]
            item["name"] = self.item_attributes["brand"]

            item["image"] = f"https://images.carbonhealth.com/{location['coverImageId']}/2x.jpg"
            item["extras"]["ref:google"] = location["googlePlaceId"]
            item["website"] = f"https://carbonhealth.com/locations/{location['slug']}"

            address = location["address"]
            item["street_address"] = merge_address_lines([address["firstLine"], address["secondLine"]])
            item["extras"]["addr:unit"] = address["aptNumber"]
            item["lat"] = address["latitude"]
            item["lon"] = address["longitude"]

            oh = OpeningHours()
            for day in location["hours"]:
                oh.add_range(DAYS[(day["day"] - 1) % 7], day["from"], day["to"])
            item["opening_hours"] = oh

            for specialty_id in location["specialtyIds"]:
                if specialty_id in specialty_id_to_speciality:
                    apply_healthcare_specialities([specialty_id_to_speciality[specialty_id]], item)
                elif specialty_id in urgent_care_specialty_ids:
                    apply_category(Categories.CLINIC_URGENT, item)
                else:
                    self.crawler.stats.inc_value(f"atp/{self.name}/unmapped_specialty/{specialty_id}")

            if any(service["name"] == "Vaccination Administration" for service in location["services"]):
                apply_healthcare_specialities([HealthcareSpecialities.VACCINATION], item)

            yield item
