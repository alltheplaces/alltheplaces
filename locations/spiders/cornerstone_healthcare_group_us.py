import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class CornerstoneHealthcareGroupUSSpider(scrapy.Spider):
    name = "cornerstone_healthcare_group_us"
    item_attributes = {"brand": "Cornerstone Healthcare Group"}
    allowed_domains = ["chghospitals.com"]
    start_urls = [
        "https://www.chghospitals.com/wp-json/wp/v2/location?per_page=100",
    ]

    def parse(self, response):
        data = response.json()

        for i, facility in enumerate(data):
            facility.update(facility.pop("acf"))
            item = DictParser.parse(facility)
            item["name"] = facility["title"]["rendered"]
            item["street_address"] = facility["address"]
            item["ref"] = item["website"] = facility["link"]
            if "Hospitals" in item["name"]:
                apply_category(Categories.HOSPITAL, item)
            else:
                apply_category({"amenity": "social_facility", "social_facility": "assisted_living"}, item)
            yield item
