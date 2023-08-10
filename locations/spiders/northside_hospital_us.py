from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.spiders.vapestore_gb import clean_address


class NorthsideHospitalUSSpider(Spider):
    name = "northside_hospital_us"
    item_attributes = {"brand": "Northside Hospital", "brand_wikidata": "Q7059745"}
    start_urls = [
        "https://locations-api.northside.production.merge-digital.com/api/LocationsSearch?page=1&pageSize=500&sortField=Name"
    ]

    categories = {
        "Cancer Services": {"healthcare:speciality": "oncology"},
        "Colorectal Surgery": {"healthcare:speciality": "proctology"},
        "Hospital": Categories.HOSPITAL,
        "Imaging Center": {"healthcare:speciality": "diagnostic_radiology"},
        "Outpatient": None,
        "Primary Care": {"healthcare": "doctor"},
        "Radiation Therapy": {"healthcare:speciality": "radiotherapy"},
        "Rehabilitation Services": {"healthcare": "rehabilitation"},
        "Specialty Care": None,
        "Spine and Pain Management": {"healthcare:speciality": "chiropractic"},
        "Surgery Center": {"healthcare:speciality": "surgery"},
        "Urgent Care": Categories.CLINIC_URGENT,
        "Vascular Surgery": {"healthcare:speciality": "vascular_surgery"},
    }

    def parse(self, response, **kwargs):
        for location in response.json()["data"]:
            location["street_address"] = clean_address([location.pop("address"), location.pop("addressLine2")])
            item = DictParser.parse(location)
            item["ref"] = location["id_string"]
            item["state"] = location["state"]["abbreviation"]
            item["image"] = location["image_url"]
            item["phone"] = location["phone_1"]
            item["website"] = location["listing_url"]

            if cat := self.categories.get(location["category"]):
                apply_category(cat, item)
            else:
                self.crawler.stats.inc_value(f'atp/northside_hospital_us/unmapped_category/{location["category"]}')
                item["extras"]["category"] = location["category"]
                # Note: also location["specialties"]

            yield item

        if next_page := response.json()["nextPageUrl"]:
            yield JsonRequest(next_page.replace("pageNumber", "page"))
