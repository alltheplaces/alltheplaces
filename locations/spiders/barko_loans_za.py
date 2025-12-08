from typing import Iterable

from chompjs import parse_js_object
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.google_url import url_to_coords
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

PROVINCES = {
    "MPUMALANGA": "Mpumalanga",
    "GAUTENG": "Gauteng",
    "LIMPOPO": "Limpopo",
    "FREE_STATE": "Free State",
    "WESTERN_CAPE": "Western Cape",
    "NORTHWEST": "North West",
    "KWAZULU_NATAL": "KwaZulu-Natal",
    "NORTHERN_CAPE": "Northern Cape",
}


class BarkoLoansZASpider(JSONBlobSpider):
    name = "barko_loans_za"
    item_attributes = {
        "brand": "Barko Loans",
        "brand_wikidata": "Q118185897",
    }
    start_urls = ["https://www.barko.co.za/Barkomap.js.txt"]
    no_refs = True

    def extract_json(self, response):
        return parse_js_object(response.text)

    def parse_feature_dict(self, response: Response, feature_dict: dict) -> Iterable[Feature]:
        for province, feature_list in feature_dict.items():
            province_name = PROVINCES.get(province)
            if province_name is None:
                province_name = province
                self.crawler.stats.inc_value(f"atp/{self.name}/unknown_province/{province}")
            for feature in feature_list:
                self.pre_process_data(feature)
                item = DictParser.parse(feature)
                item["state"] = province_name
                yield from self.post_process_item(item, response, feature) or []

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["street_address"] = location["officeAddress"]
        item["phone"] = location.get("officeNumber")
        item["lat"], item["lon"] = url_to_coords(location.get("googleOfficeAddress"))

        yield item
