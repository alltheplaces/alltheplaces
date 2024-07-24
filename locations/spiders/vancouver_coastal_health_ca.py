import json

from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class VancouverCoastalHealthCASpider(Spider):
    name = "vancouver_coastal_health_ca"
    item_attributes = {"brand": "Vancouver Coastal Health", "brand_wikidata": "Q7914144"}
    start_urls = ["https://www.vch.ca/en/find-location"]

    CATEGORIES = {
        "0": Categories.HOSPITAL,
        "1": Categories.CLINIC_URGENT,
        "2": {"amenity": "healthcare", "healthcare": "centre", "healthcare:speciality": "community"},
        "3": Categories.NURSING_HOME,
        "4": {"amenity": "social_facility", "social_facility": "assisted_living"},
        "5": Categories.HOSPICE,
        "7": {"amenity": "healthcare", "healthcare": "psychotherapist"},
        "8": {"amenity": "social_facility", "social_facility:for": "mental_health"},
        "10": {"amenity": "healthcare", "healthcare": "vaccination_centre"},
        "11": {"amenity": "healthcare", "healthcare": "counselling", "healthcare:counselling": "addiction"},
        "12": {"office": "yes"},  # "Environmental health \\u0026 inspections offices",
        "13": {"amenity": "healthcare", "healthcare": "centre"},  # "Other",
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

            yield item
