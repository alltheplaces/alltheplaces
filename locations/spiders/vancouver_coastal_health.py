import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class VancouverCoastalHealthSpider(Spider):
    name = "vancouver_coastal_health"
    item_attributes = {"brand": "Vancouver Coastal Health", "brand_wikidata": "Q7914144"}
    start_urls = ["https://www.vch.ca/en/find-location"]

    CATEGORIES = {
        "0": Categories.HOSPITAL,
        "1": None,  # "Urgent \\u0026 primary care centres",
        "2": None,  # "Community health centres",
        "3": None,  # "Long term care homes",
        "4": {"amenity": "social_facility", "social_facility": "assisted_living"},
        "5": {"healthcare": "hospice"},
        "7": {"healthcare": "psychotherapist"},
        "8": None,  # "Crisis intervention facilities",
        "10": None,  # "Travel clinics",
        "11": None,  # "Harm reduction site",
        "12": None,  # "Environmental health \\u0026 inspections offices",
        "13": None,  # "Other",
    }

    def parse(self, response, **kwargs):
        data = json.loads(response.xpath('//script[contains(., "find_location")]/text()').get())

        for location in data["vch"]["find_location"]["locations"]:
            location["location"] = location.pop("coords")
            location["ref"] = location["nid"]
            location["address"]["street_address"] = location["address"].pop("line_1")
            location["url"] = f'https://www.vch.ca{location["url"]}'

            item = DictParser.parse(location)
            item["image"] = location["image"]

            if cat := self.CATEGORIES.get(location["type"]["id"]):
                apply_category(cat, item)

            item["country"] = "CA"

            yield item
