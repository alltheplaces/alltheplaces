import scrapy
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class DepartmentVeteransAffairsSpider(scrapy.Spider):
    name = "department_veterans_affairs"
    item_attributes = {"brand": "Department Veterans Affairs", "brand_wikidata": "Q592576"}
    allowed_domains = ["api.va.gov"]

    def start_requests(self):
        data = {
            "page": 1,
            "per_page": 1000,
            "mobile": False,
            "radius": 1000,
            "bbox": ["-180", "-90", "180", "90"],
            "latitude": "0",
            "longitude": "0",
        }
        yield JsonRequest(
            "https://api.va.gov/facilities_api/v2/va",
            data=data,
            callback=self.parse_info,
        )

    def parse_info(self, response):
        resp_json = response.json()

        data = resp_json["data"]
        types = {}
        facitlity_types = {}

        for row in data:
            place_info = row["attributes"]

            if row["type"] not in types:
                types[row["type"]] = 1
            else:
                types[row["type"]] += 1

            if place_info["facilityType"] not in facitlity_types:
                facitlity_types[place_info["facilityType"]] = 1
            else:
                facitlity_types[place_info["facilityType"]] += 1

            item = DictParser.parse(place_info)
            item["ref"] = row["id"]
            item["country"] = "US"
            self.parse_address(item, place_info)
            if not isinstance(place_info.get("phone"), list):
                item["phone"] = place_info.get("phone", {}).get("main")
                item["extras"]["fax"] = place_info.get("phone", {}).get("fax")
            item["extras"]["type"] = row["type"]
            item["opening_hours"] = self.parse_hours(place_info.get("hours"))

            if "clinic" in item["name"].lower():
                apply_category(Categories.CLINIC, item)
            elif "hospital" in item["name"].lower():
                apply_category(Categories.HOSPITAL, item)
            elif "urgent care" in item["name"].lower():
                apply_category(Categories.CLINIC_URGENT, item)
            else:
                apply_category(Categories.CLINIC, item)

            yield item

        if next_url := resp_json["links"]["next"]:
            yield JsonRequest(next_url, callback=self.parse_info, method="POST")

    def parse_address(self, item: Feature, place_info: dict):
        addr = place_info["address"]
        if "physical" in addr:
            addr = place_info["address"]["physical"]
        elif "mailing" in addr:
            addr = place_info["address"]["mailing"]
        if addr:
            item["street_address"] = merge_address_lines(
                [addr.get("address1"), addr.get("address2"), addr.get("address3")]
            )
            item["city"] = addr.get("city")
            item["state"] = addr.get("state")
            item["postcode"] = addr.get("zip")

    def parse_hours(self, hours):
        if not hours:
            return None

        opening_hours = OpeningHours()

        if hours.get("monday") == "24/7":
            return "24/7"

        for day, hours in hours.items():
            day = day[:2].lower()
            try:
                open_time, close_time = hours.split("-")
                opening_hours.add_range(day, open_time=open_time, close_time=close_time, time_format="%I%M%p")
            except:
                continue

        return opening_hours.as_opening_hours()
