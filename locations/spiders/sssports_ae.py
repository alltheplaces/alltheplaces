from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class SssportsAESpider(Spider):
    name = "sssports_ae"
    item_attributes = {"brand": "SS Sports", "brand_wikidata": "Q133263395"}

    start_urls = ["https://en-ae.sssports.com/on/demandware.store/Sites-UAE-Site/en_AE/Stores-FindStores?showMap=true&city=all&all"]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location.get("ID")

            # Build street address
            address_parts = []
            if location.get("address1"):
                address_parts.append(location["address1"])
            if location.get("address2"):
                address_parts.append(location["address2"])
            item["street_address"] = ", ".join(address_parts) if address_parts else None

            # Parse hours
            if store_hours := location.get("storeHours"):
                oh = OpeningHours()
                for day_data in store_hours:
                    day = day_data.get("name", "").title()[:2]
                    start = day_data.get("start")
                    end = day_data.get("end")
                    if day and start and end:
                        oh.add_range(day, start, end)
                item["opening_hours"] = oh

            if location.get("countryCode") == "UA":
                item["country"] = "AE"

            apply_category(Categories.SHOP_CLOTHES, item)

            yield item
