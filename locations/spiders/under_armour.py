from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class UnderArmourSpider(Spider):
    name = "under_armour"
    item_attributes = {"brand": "Under Armour", "brand_wikidata": "Q2031485"}
    allowed_domains = ["store-locator.underarmour.com"]

    def start_requests(self):
        yield JsonRequest(url="https://store-locator.underarmour.com/api/stores/nearby/?lat=0&lng=0&radius=50000")

    def parse(self, response: Response, **kwargs: Any):
        for store in response.json()["stores"]:
            if store.get("store_type") == "Dealer":
                continue
            if store.get("openInfo") == "CLOSED_PERMANENTLY":
                continue

            item = DictParser.parse(store)
            item["branch"] = (
                item.pop("name").removeprefix("UNDER ARMOUR ").removeprefix("Under Armour ").removeprefix("UA ")
            )
            if item["branch"].startswith("BRAND HOUSE ") or item["branch"].startswith("Brand House "):
                item["name"] = "Under Armour Brand House"
                item["branch"] = item["branch"][12:].strip("- ")
            elif "Factory House" in item["branch"]:
                item["name"] = "Under Armour Factory House"
                item["branch"] = item["branch"].replace("Factory House", "").strip(" |-")
            else:
                item["name"] = "Under Armour"
                item["branch"] = item["branch"].strip("- ")
            item["street"] = None
            item["street_address"] = merge_address_lines(
                [store["address"].get("street"), store["address"].get("street2")]
            )
            item["website"] = f"https://store-locator.underarmour.com/en-us/store/{store['id']}/"

            self._parse_hours(item, store)

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item

    def _parse_hours(self, item, store: dict):
        hours = store.get("hours", {})
        if not hours:
            return
        try:
            oh = OpeningHours()
            fail_count = 0
            for day in DAYS_FULL:
                value = hours.get(day.lower(), "")
                if not value or value == "Closed":
                    continue
                try:
                    oh.add_ranges_from_string(f"{day} {value}")
                except Exception:
                    fail_count += 1
                    if fail_count >= 3:
                        break
            item["opening_hours"] = oh
        except Exception:
            self.crawler.stats.inc_value("atp/hours/failed")
