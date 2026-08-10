from copy import deepcopy
from typing import Iterable

import chompjs
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS_RU, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiUASpider(JSONBlobSpider):
    name = "mitsubishi_ua"
    item_attributes = {"brand": "Mitsubishi", "brand_wikidata": "Q36033"}
    start_urls = ["https://mitsubishi-motors.com.ua/find-a-dealer"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def extract_json(self, response: Response) -> list[dict]:
        return chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "window.__NUXT__")]/text()').re_first(
                r"dealers\s*=\s*\'(\[.+?\])\'"
            ),
            unicode_escape=True,
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["lat"], item["lon"] = feature["latlng"].split(",")
        item["street_address"] = item.pop("addr_full", None)
        item["website"] = feature.get("website_link")
        item["extras"]["brand:website"] = response.urljoin(f'?dealer={item["ref"]}')

        departments = {
            department["title"]: {
                "phones": department["phones"],
                "email": department["email"],
                "schedule": department["schedule"],
            }
            for department in feature["departments"]
        }
        SALES = "Відділ продажу"
        SERVICE = "Відділ сервісу"

        if SALES in departments:
            sales_item = deepcopy(item)
            sales_item["ref"] = f"{item['ref']}-sales"
            dept = departments[SALES]
            sales_item["phone"] = (dept.get("phones") or "").replace(",", "; ")
            sales_item["email"] = dept.get("email")
            oh = OpeningHours()
            for rule in dept.get("schedule", []):
                oh.add_ranges_from_string(f'{rule["day"]} {rule["workhours"]}', days=DAYS_RU)
            sales_item["opening_hours"] = oh
            apply_category(Categories.SHOP_CAR, sales_item)
            apply_yes_no(Extras.CAR_REPAIR, sales_item, SERVICE in departments)
            yield sales_item

        if SERVICE in departments:
            service_item = deepcopy(item)
            service_item["ref"] = f"{item['ref']}-service"
            dept = departments[SERVICE]
            service_item["phone"] = (dept.get("phones") or "").replace(",", "; ")
            service_item["email"] = dept.get("email")
            oh = OpeningHours()
            for rule in dept.get("schedule", []):
                oh.add_ranges_from_string(f'{rule["day"]} {rule["workhours"]}', days=DAYS_RU)
            service_item["opening_hours"] = oh
            apply_category(Categories.SHOP_CAR_REPAIR, service_item)
            yield service_item
