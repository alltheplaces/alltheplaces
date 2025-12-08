from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class UnderArmourAESASpider(Spider):
    name = "under_armour_ae_sa"
    item_attributes = {
        "brand": "Under Armour",
        "brand_wikidata": "Q2031485",
    }
    allowed_domains = ["underarmour.ae", "underarmour.sa"]

    def start_requests(self):
        urls = [
            # UAE stores
            "https://www.underarmour.ae/on/demandware.store/Sites-UnderArmour_AE-Site/en_AE/Stores-FindStores?showMap=true&selectedCountry=AE&city=all",
            # Saudi Arabia stores
            "https://www.underarmour.sa/on/demandware.store/Sites-UnderArmour_SA-Site/en_SA/Stores-FindStores?showMap=true&selectedCountry=SA&city=all",
        ]

        for url in urls:
            country_code = "SA" if "underarmour.sa" in url else "AE"
            yield JsonRequest(url=url, meta={"country": country_code})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().get("stores", []):
            item = DictParser.parse(store)
            item["ref"] = store.get("ID")

            # Clean up phone number
            if phone := store.get("phone"):
                if phone.startswith("Phone"):
                    item["phone"] = phone[5:].strip()

            # Build street address
            address_parts = []
            if store.get("address1"):
                address_parts.append(store["address1"])
            if store.get("address2"):
                address_parts.append(store["address2"])
            item["street_address"] = ", ".join(address_parts) if address_parts else None

            # Parse hours
            if store_hours := store.get("storeHours"):
                oh = OpeningHours()
                for day_data in store_hours:
                    day = day_data.get("name", "").title()[:2]
                    start = day_data.get("start")
                    end = day_data.get("end")
                    if day and start and end:
                        oh.add_range(day, start, end)
                item["opening_hours"] = oh.as_opening_hours()

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
