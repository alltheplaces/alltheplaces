import re
from typing import Iterable
from urllib.parse import urljoin

from chompjs import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class AutoNationUSSpider(JSONBlobSpider, PlaywrightSpider):
    name = "auto_nation_us"
    allowed_domains = ["autonation.com"]
    item_attributes = {"brand": "AutoNation", "brand_wikidata": "Q784804"}
    # Any dealer page like https://www.autonation.com/dealers/land-rover-bethesda contains this "StoreDetailsPage/main-*.js" file, which holds the list of all dealers
    start_urls = ["https://www.autonation.com/dealers/public/dist/StoreDetailsPage/main-2ZVLGVZJ.js"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS | {"PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 180 * 1000}

    def extract_json(self, response: TextResponse) -> dict | list[dict]:
        return chompjs.parse_js_object(
            re.search(r"serviceStoresList:(\[.+])[,\s]+offers", response.text).group(1), unicode_escape=True
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("hyperionId")

        website = (item.get("website") or "").replace("null", "")
        if not website.startswith("https://www.autonation.com") and "autonation.com" in website:
            item["website"] = urljoin("https://www.autonation.com", website.split("autonation.com")[1])
        else:
            item["website"] = website

        hours = feature.get("detailedHours") or []

        departments = feature.get("departments") or []
        department_types = [department.get("name") for department in departments]
        for department in departments:
            if department.get("name") == "Sales":
                sales_item = item.deepcopy()
                sales_item["ref"] = "{}-sales".format(sales_item["ref"])
                sales_item["opening_hours"] = self.parse_opening_hours(department.get("detailedHours") or hours)
                apply_category(Categories.SHOP_CAR, sales_item)
                yield sales_item

            elif department.get("name") == "Service":
                service_item = item.deepcopy()
                service_item["ref"] = "{}-service".format(service_item["ref"])
                service_item["opening_hours"] = self.parse_opening_hours(department.get("detailedHours") or hours)
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item

            elif department.get("name") == "Collision" and "Service" not in department_types:
                service_item = item.deepcopy()
                service_item["ref"] = "{}-service".format(service_item["ref"])
                service_item["opening_hours"] = self.parse_opening_hours(department.get("detailedHours") or hours)
                apply_category(Categories.SHOP_CAR_REPAIR, service_item)
                yield service_item

        if not any(department_type in department_types for department_type in ["Sales", "Service", "Collision"]):
            self.logger.warning("Unknown feature type from provided departments: {}".format(";".join(department_types)))

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day = DAYS[rule["day"]]
            if rule.get("startTime") and rule.get("endTime"):
                oh.add_range(day, rule["startTime"], rule["endTime"], "%I:%M %p")
            else:
                oh.set_closed(day)
        return oh
