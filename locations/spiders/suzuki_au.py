import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SuzukiAUSpider(JSONBlobSpider):
    name = "suzuki_au"
    item_attributes = {"brand": "Suzuki", "brand_wikidata": "Q181642"}
    allowed_domains = ["www.suzuki.com.au"]
    start_urls = ["https://www.suzuki.com.au/sites/default/files/staticly/dynamic-data/dealers.json"]
    locations_key = "dealers"

    def pre_process_data(self, feature: dict) -> None:
        feature.update(feature.pop("data"))

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        for department, category in (("sales", Categories.SHOP_CAR), ("service", Categories.SHOP_CAR_REPAIR)):
            department_data = feature.get(department)
            if not department_data:
                continue

            location = department_data.get("location") or feature["location"]
            contact = department_data.get("contact") or {}
            location_item = DictParser.parse(
                {
                    "ref": f"{feature['code'].strip()}_{department}",
                    "name": feature["name"],
                    "street_address": location.get("street"),
                    "suburb": location.get("suburb"),
                    "state": location.get("state"),
                    "postcode": location.get("postcode"),
                    "latitude": location.get("geo", {}).get("latitude"),
                    "longitude": location.get("geo", {}).get("longitude"),
                    "phone": contact.get("phone"),
                    "website": "https://www.suzuki.com.au" + feature["url"],
                }
            )
            location_item["branch"] = location_item.pop("name")
            location_item["opening_hours"] = self.parse_hours(department_data.get("hours", []))
            apply_category(category, location_item)
            yield location_item

    @staticmethod
    def parse_hours(rules: list[dict]) -> OpeningHours:
        hours = OpeningHours()
        for rule in rules:
            if rule.get("open") is False or rule.get("close") is False:
                hours.set_closed(rule["day"])
            else:
                hours.add_range(
                    rule["day"],
                    SuzukiAUSpider.normalise_time(rule["open"]),
                    SuzukiAUSpider.normalise_time(rule["close"]),
                    "%I:%M%p",
                )
        return hours

    @staticmethod
    def normalise_time(value: str) -> str:
        value = re.sub(r"\s*\(.*", "", value).strip().lower().replace(".", ":")
        return re.sub(r"^(\d{1,2})(am|pm)$", r"\1:00\2", value)
