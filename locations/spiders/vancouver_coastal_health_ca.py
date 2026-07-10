from json import loads

from scrapy import Spider

from locations.categories import Categories, HealthcareSpecialities, apply_category, apply_healthcare_specialities
from locations.dict_parser import DictParser


class VancouverCoastalHealthCASpider(Spider):
    name = "vancouver_coastal_health_ca"
    item_attributes = {"operator": "Vancouver Coastal Health", "operator_wikidata": "Q7914144"}
    start_urls = ["https://www.vch.ca/en/locations"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    _category_map = {
        "0": (Categories.HOSPITAL, []),  # Hospitals
        "1": (Categories.CLINIC_URGENT, []),  # Urgent & primary care centres
        "2": (Categories.CLINIC, [HealthcareSpecialities.COMMUNITY]),  # Community health centres
        "3": (Categories.NURSING_HOME, []),  # Long term care homes
        "4": (Categories.ASSISTED_LIVING, []),  # Assisted living
        "5": (Categories.HOSPICE, []),  # Hospices
        "7": (Categories.CLINIC, [HealthcareSpecialities.PSYCHIATRY]),  # Mental health clinics
        "8": (Categories.HOSPITAL, [HealthcareSpecialities.PSYCHIATRY]),  # Crisis intervention facilities
        "9": (Categories.OFFICE_HEALTHCARE, []),  # Home health & support
        "10": (Categories.VACCINATION_CENTRE, []),  # Travel clinics
        "11": (Categories.OFFICE_SUPERVISED_INJECTION_SITE, []),  # Harm reduction site
        "12": (Categories.OFFICE_HEALTHCARE, []),  # Environmental health & inspections offices
        "13": (Categories.CLINIC, []),  # Other
        # 14 - unused / unspecified
        # 15 - "Service": ignore, generally not physical features
        # 16 - "Program": ignore, generally not physical features
    }

    def parse(self, response, **kwargs):
        data = loads(response.xpath('//script[contains(., "find_location")]/text()').get())

        for location in data["vch"]["find_location"]["locations"]:
            location["location"] = location.pop("coords")
            location["ref"] = location["nid"]
            location["address"]["street_address"] = location["address"].pop("line_1")
            location["url"] = f'https://www.vch.ca{location["url"]}'

            item = DictParser.parse(location)
            if img := location.get("image"):
                # Filter generic placeholder images that appear on most locations
                if "Mountains_pattern" not in img and "VCH_pattern" not in img:
                    item["image"] = img

            if cat := self._category_map.get(location["type"]["id"]):
                apply_category(cat[0], item)
                apply_healthcare_specialities(cat[1], item)
            elif location["type"]["id"] in ["14", "15", "16"] or not location["type"]["id"].strip():
                # Categories ignored as not used / generally not physical features.
                continue
            else:
                self.logger.warning("Unknown category code: {}".format(location["type"]["id"]))

            yield item
