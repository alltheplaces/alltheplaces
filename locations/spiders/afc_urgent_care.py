from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines
from locations.user_agents import BROWSER_DEFAULT


class AfcUrgentCareSpider(JSONBlobSpider):
    name = "afc_urgent_care"
    item_attributes = {"operator": "AFC Urgent Care", "operator_wikidata": "Q110552174"}
    allowed_domains = ["afcurgentcare.com"]
    start_urls = ("https://www.afcurgentcare.com/modules/multilocation/?near_lat=39&near_lon=-98&limit=1000",)
    locations_key = "objects"
    custom_settings = {"USER_AGENT": BROWSER_DEFAULT}

    def pre_process_data(self, feature: dict) -> None:
        feature["street_address"] = merge_address_lines([feature.pop("street", None), feature.pop("street2", None)])
        feature["website"] = feature.pop("location_url", None)
        feature["phone"] = feature.pop("phonemap_e164", {}).get("phone")

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if not item.get("street_address"):
            return  # Skip state-level placeholder entries

        if hours := feature.get("hours_of_operation"):
            item["opening_hours"] = OpeningHours()
            for (h, _), day in zip(hours, DAYS):
                if h:
                    item["opening_hours"].add_range(day, h[0], h[1], "%H:%M:%S")
        yield item
