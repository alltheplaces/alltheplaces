from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.geo import postal_regions
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.hyundai_kr import HYUNDAI_SHARED_ATTRIBUTES


class HyundaiUSSpider(JSONBlobSpider):
    name = "hyundai_us"
    item_attributes = HYUNDAI_SHARED_ATTRIBUTES
    allowed_domains = ["www.hyundaiusa.com"]

    def start_requests(self):
        for index, record in enumerate(postal_regions("US")):
            if index % 100 == 0:
                yield JsonRequest(
                    url=f'https://www.hyundaiusa.com/var/hyundai/services/dealer/dealersByZip.json?brand=hyundai&model=all&lang=en_US&radius=150&zip={record["postal_region"]}',
                    headers={"Referer": "https://www.hyundaiusa.com/us/en/dealer-locator"},
                )

    def extract_json(self, response: Response) -> dict | list:
        return response.json().get("dealers", [])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["name"] = feature.get("dealerNm")
        item["street_address"] = clean_address([feature.get("address1"), feature.get("address2")])
        item["postcode"] = feature.get("zipCd")
        item["email"] = feature.get("dealerEmail")
        item["website"] = feature.get("dealerUrl")
        if item["website"] and item["website"].startswith("www."):
            item["website"] = "https://" + item["website"]

        if "showroom" in feature.keys():
            sales = item.deepcopy()
            apply_category(Categories.SHOP_CAR, sales)
            sales["ref"] = feature["dealerCd"] + "_Sales"
            sales["opening_hours"] = self.parse_opening_hours(feature, "showroom")
            yield sales

        if "operations" in feature.keys():
            service = item.deepcopy()
            apply_category(Categories.SHOP_CAR_REPAIR, service)
            service["ref"] = feature["dealerCd"] + "_Service"
            service["opening_hours"] = self.parse_opening_hours(feature, "operations")
            yield service
            parts = item.deepcopy()
            apply_category(Categories.SHOP_CAR_PARTS, parts)
            parts["ref"] = feature["dealerCd"] + "_Parts"
            parts["opening_hours"] = self.parse_opening_hours(feature, "operations")
            yield parts

    def parse_opening_hours(self, feature: dict, hours_type: str) -> OpeningHours:
        oh = OpeningHours()
        if hours := feature.get(hours_type):
            for day_hours in hours:
                if day_hours["hour"] == "Closed":
                    oh.set_closed(day_hours["day"])
                else:
                    oh.add_range(day_hours["day"], *day_hours["hour"].split(" - ", 1), "%I:%M %p")
        return oh
