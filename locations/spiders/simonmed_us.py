from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines


class SimonmedUSSpider(JSONBlobSpider):
    name = "simonmed_us"
    item_attributes = {"brand": "SimonMed"}
    start_urls = ["https://simonmed.com/wp-json/brandpie/v1/locations"]

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("sm-location_address_group", None) or {})
        feature.update(feature.pop("sm-latitude_longitude", None) or {})
        feature["street_address"] = merge_address_lines(
            [feature.pop("street_address_1", None), feature.pop("street_address_2", None)]
        )
        feature["phone"] = (feature.get("sm-contact_numbers") or {}).get("phone_number")
        feature["website"] = feature.pop("link", None)
        feature["ref"] = feature.pop("ID", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["opening_hours"] = OpeningHours()
        for day_name, rule in (feature.get("sm-timing") or {}).items():
            if not (day := sanitise_day(day_name)) or not isinstance(rule, dict):
                continue
            if rule.get("show_time"):
                item["opening_hours"].add_ranges_from_string(
                    f'{day} {rule.get("opening_time")} - {rule.get("closing_time")}'
                )
            elif not rule.get("closed_text"):
                item["opening_hours"].set_closed(day)
        apply_category(Categories.MEDICAL_IMAGING, item)
        yield item
