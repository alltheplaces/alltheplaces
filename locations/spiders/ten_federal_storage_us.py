from typing import Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class TenFederalStorageUSSpider(Spider):
    name = "ten_federal_storage_us"
    item_attributes = {"brand": "10 Federal Storage"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://10federalstorage.com/api/facilities?limit=500&depth=0&where[hidden][equals]=false"
        "&select[name]=true&select[slug]=true&select[storedgeData]=true"
    ]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for facility in response.json()["docs"]:
            location = facility["storedgeData"]
            if location["brand_name"] != "10 Federal Storage" or not facility.get("slug"):
                continue
            item = DictParser.parse(location)
            item["ref"] = facility["id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lng"]
            item["street_address"] = location["address"]["address1"].strip()
            item["postcode"] = location["address"]["postal"]
            item["email"] = None
            item["website"] = f"https://10federalstorage.com/storage-units/{facility['slug']}"

            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                hours = (location.get("office_hours") or {}).get(day.lower())
                if hours:
                    item["opening_hours"].add_ranges_from_string(f"{day} {hours['hoursString']}")

            apply_category(Categories.SHOP_STORAGE_RENTAL, item)
            yield item
