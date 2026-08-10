import datetime
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class NikeSpider(Spider):
    name = "nike"
    item_attributes = {"brand": "Nike", "brand_wikidata": "Q483915"}
    start_urls = ["https://nslp-directory.nike.com/store-locations-static.json"]

    def extract_image(self, item: Feature, store: dict) -> None:
        placeholders = [
            "2e8d9338-b43d-4ef5-96e1-7fdcfd838f8e",
            "d2f5c06a-629d-4f20-a092-9e56315a80b3",
            "fvnjv5WPReybS5kbv4tg",
            "95cdf0dc-b6a1-4c87-a5fd-b374fca525e4",
            "ce9b47ad-af3e-4c4b-a500-9ed12969440e",
            "ed1a0204-614e-4e62-9d1b-1754dd9afe2c",
            "fa253650-9040-44ac-91e9-7b7175f1cc3f",
        ]
        # Ignore generic placeholder image used when a store-specific
        # image is not provided.
        if store.get("imageURL"):
            for placeholder_pattern in placeholders:
                if placeholder_pattern in store["imageURL"]:
                    return

            item["image"] = store["imageURL"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        all_stores = response.json()["stores"]
        for store in all_stores.values():
            item = DictParser.parse(store)
            item["name"] = self.item_attributes["brand"]
            item["opening_hours"] = self.parse_opening_hours(DictParser.get_nested_key(store, "regularHours"))

            if re.match(r"^[A-Za-z0-9_-]+$", store["slug"]):
                item["website"] = "https://www.nike.com/retail/s/" + store["slug"]
            else:
                item["website"] = None

            self.extract_image(item, store)

            item["extras"] = {"owner:type": store["facilityType"]}
            if store["businessConcept"] == "FACTORY":
                item["brand"] = "Nike Factory Store"
            elif store["businessConcept"] == "CLEARANCE":
                item["brand"] = "Nike Clearance Store"
            elif store["businessConcept"] == "COMMUNITY":
                item["brand"] = "Nike Community Store"
            else:
                item["extras"]["type"] = store["businessConcept"]

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item

    def parse_opening_hours(self, hours: dict) -> OpeningHours:
        opening_hours = OpeningHours()
        for day in hours:
            if not hours.get(day):
                continue

            oh = hours.get(day)[0]
            opening = oh.get("startTime")
            closing = oh.get("duration")

            closing_h = closing.split("H")[0].replace("PT", "") if "H" in closing else "0"
            closing_m = closing[len(closing) - 3 :].replace("M", "") if "M" in closing else "0"
            closing_m = closing_m.replace("H", "")  # needed for 1 digit minutes

            start = opening.split(":")
            closing_time = str(
                datetime.timedelta(hours=int(start[0]), minutes=int(start[1]))
                + datetime.timedelta(hours=int(closing_h), minutes=int(closing_m))
            )
            if "day" in closing_time:
                closing_time = "00:00"
            else:
                split_closing_time = closing_time.split(":")
                closing_time = "".join(split_closing_time[0] + ":" + split_closing_time[1])

            opening_hours.add_range(day[0:2].title(), opening, closing_time)
        return opening_hours
