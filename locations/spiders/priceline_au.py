from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address

PHARMACY_BRAND = {"brand": "Priceline Pharmacy", "brand_wikidata": "Q7242652"}
STORE_BRAND = {"brand": "Priceline", "brand_wikidata": "Q7242652"}


class PricelineAUSpider(Spider):
    name = "priceline_au"
    item_attributes = PHARMACY_BRAND
    allowed_domains = ["api.priceline.com.au"]

    async def start(self) -> AsyncIterator[JsonRequest]:
        # The store search API requires a lat/lon origin and does not expose a
        # plain paginated listing of all stores, so a spread of populated
        # places is used as search origins and duplicate stores (by their
        # stable store code) are dropped by the standard dedupe pipeline.
        for city in city_locations("AU", 15000):
            yield JsonRequest(
                url="https://api.priceline.com.au/occ/v2/priceline/stores"
                f"?accuracy=0&currentPage=0&fields=FULL&latitude={city['latitude']}&longitude={city['longitude']}"
                "&pageSize=1000&pharmacyStore=false&radius=999999&sort=asc&lang=en&curr=AUD",
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json().get("stores", []):
            if location.get("suspended"):
                continue
            if "coming soon" in location["displayName"].lower():
                continue

            address = location.get("address", {})

            item = DictParser.parse(location)
            item["ref"] = location["name"]
            item["street_address"] = clean_address([address.get("line1"), address.get("line2")])
            item.pop("street", None)
            item["state"] = address.get("region", {}).get("isocodeShort")
            item["phone"] = address.get("phone")
            item["email"] = address.get("email")
            item["website"] = "https://www.priceline.com.au" + location["url"].split("?")[0]

            display_name = location["displayName"].strip()
            if location.get("type") == "STORE":
                item.update(STORE_BRAND)
                item["name"] = STORE_BRAND["brand"]
                item["branch"] = display_name.removeprefix("Priceline").strip()
                apply_category(Categories.SHOP_CHEMIST, item)
            else:
                item.update(PHARMACY_BRAND)
                item["name"] = PHARMACY_BRAND["brand"]
                item["branch"] = display_name.removeprefix("Priceline Pharmacy").strip()
                apply_category(Categories.PHARMACY, item)

            item["opening_hours"] = self.parse_opening_hours(location["openingHours"]["weekDayOpeningList"])

            yield item

    @staticmethod
    def parse_opening_hours(rules: list[dict]) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            if rule.get("closed"):
                continue
            # Some days are marked open with a zeroed out, meridiem-less
            # time instead of being flagged "closed" - treat these as closed.
            if "meridiemIndicator" not in rule["openingTime"] or "meridiemIndicator" not in rule["closingTime"]:
                continue
            oh.add_range(
                rule["weekDay"],
                PricelineAUSpider.format_time(rule["openingTime"]),
                PricelineAUSpider.format_time(rule["closingTime"]),
            )
        return oh

    @staticmethod
    def format_time(t: dict) -> str:
        # Source gives a 12 hour "hour" (1-12) plus an AM/PM indicator.
        hour = t["hour"] % 12
        if t["meridiemIndicator"] == "PM":
            hour += 12
        return f"{hour:02d}:{t['minute']:02d}"
