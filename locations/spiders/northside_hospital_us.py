import chompjs
from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import merge_address_lines
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS
from locations.user_agents import BROWSER_DEFAULT


class NorthsideHospitalUSSpider(Spider):
    name = "northside_hospital_us"
    item_attributes = {"brand": "Northside Hospital", "brand_wikidata": "Q7059745"}
    start_urls = ["https://locations-api-prod.northside.com/api/LocationsSearch?&Page=1&PageSize=10"]
    is_playwright_spider = True
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    categories = {
        "Cancer Services": {"amenity": "hospital", "healthcare": "hospital", "healthcare:speciality": "oncology"},
        "Colorectal Surgery": {"amenity": "hospital", "healthcare": "hospital", "healthcare:speciality": "proctology"},
        "Hospital": Categories.HOSPITAL,
        "Imaging Center": {
            "amenity": "clinic",
            "healthcare": "clinic",
            "healthcare:speciality": "diagnostic_radiology",
        },
        "Outpatient": Categories.CLINIC,
        "Primary Care": Categories.DOCTOR_GP,
        "Radiation Therapy": {"amenity": "hospital", "healthcare": "hospital", "healthcare:speciality": "radiotherapy"},
        "Rehabilitation Services": {"amenity": "clinic", "healthcare": "rehabilitation"},
        "Specialty Care": Categories.CLINIC,
        "Spine and Pain Management": {
            "amenity": "clinic",
            "healthcare": "clinic",
            "healthcare:speciality": "chiropractic",
        },
        "Surgery Center": {"amenity": "hospital", "healthcare": "hospital", "healthcare:speciality": "surgery"},
        "Urgent Care": Categories.CLINIC_URGENT,
        "Vascular Surgery": {
            "amenity": "hospital",
            "healthcare": "hospital",
            "healthcare:speciality": "vascular_surgery",
        },
    }

    def parse(self, response, **kwargs):
        json_response = chompjs.parse_js_object(response.text)  # Extract JSON from HTML Response
        for location in json_response["data"]:
            location["street_address"] = merge_address_lines([location.pop("address"), location.pop("addressLine2")])
            item = DictParser.parse(location)
            item["ref"] = location["id_string"]
            item["state"] = location["state"]["abbreviation"]
            item["image"] = location["image_url"]
            item["phone"] = location["phone_1"]
            item["website"] = location["listing_url"]

            if cat := self.categories.get(location["category"]):
                apply_category(cat, item)
            else:
                apply_category(Categories.CLINIC, item)

            yield item

        if next_page := json_response["nextPageUrl"]:
            yield JsonRequest(next_page.replace("pageNumber", "page"))
