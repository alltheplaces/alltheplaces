from typing import Any, Iterable

import chompjs
from scrapy.http import TextResponse

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import merge_address_lines

BRAND_PREFIXES = ["Peoples Bank", "People's Bank", "People’s Bank"]
CUSTOMER_SERVICE_PHONE = "(800) 374-6123"


class PeoplesBankUSSpider(JSONBlobSpider):
    name = "peoples_bank_us"
    item_attributes = {"brand": "Peoples Bank", "brand_wikidata": "Q65716607"}
    start_urls = ["https://www.peoplesbancorp.com/locations/"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        return chompjs.parse_js_object(response.xpath('//script[@id="pebo-map-locator-js-before"]/text()').get())[
            "locations"
        ]

    def post_process_item(
        self, item: Feature, response: TextResponse, location: dict, **kwargs: Any
    ) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
        item["branch"] = self.clean_branch(item.pop("name"))
        if item["phone"] == CUSTOMER_SERVICE_PHONE:
            item["phone"] = None
        item["opening_hours"] = self.parse_hours(location["hours"]["primary"])

        location_type = location["type"]
        if location_type == "24 hour ATM":
            apply_category(Categories.ATM, item)
            item["operator"] = self.item_attributes["brand"]
            item["operator_wikidata"] = self.item_attributes["brand_wikidata"]
            if item["branch"]:
                item["branch"] = item["branch"].removeprefix("24 HR ATM").lstrip(" –") or None
        elif location_type == "Insurance Location":
            item["name"] = self.item_attributes["brand"]
            apply_category(Categories.OFFICE_INSURANCE, item)
        elif "office" in location["title"].lower():
            item["name"] = self.item_attributes["brand"]
            apply_category(Categories.OFFICE_FINANCIAL, item)
        else:
            if location_type not in ["Branch", "Branch & ATM", "Drive thru & ATM"]:
                self.crawler.stats.inc_value(f"atp/{self.name}/unmapped_type/{location_type}")
            item["name"] = self.item_attributes["brand"]
            apply_category(Categories.BANK, item)

        if location_type in ["Branch & ATM", "Drive thru & ATM"]:
            apply_yes_no(Extras.ATM, item, True)
            if atm_hours := self.parse_hours(location["hours"]["atm"]):
                item["extras"]["opening_hours:atm"] = atm_hours.as_opening_hours()

        if drive_through_hours := self.parse_hours(location["hours"]["driveThru"]):
            apply_yes_no(Extras.DRIVE_THROUGH, item, True)
            item["extras"]["opening_hours:drive_through"] = drive_through_hours.as_opening_hours()

        yield item

    @staticmethod
    def clean_branch(title: str) -> str | None:
        for prefix in BRAND_PREFIXES:
            if title.startswith(prefix):
                return title.removeprefix(prefix).strip(" –") or None
        return title

    @staticmethod
    def parse_hours(rules: dict) -> OpeningHours | None:
        opening_hours = OpeningHours()
        for day, rule in rules.items():
            if rule["open"] == "By Appointment Only":
                continue
            elif rule["open"] == "0:00" and rule["close"] == "0:00":
                # The locator renders a midnight to midnight range as "Open 24 Hours".
                opening_hours.add_range(day, "00:00", "23:59")
            else:
                opening_hours.add_range(day, rule["open"], rule["close"])
        return opening_hours or None
