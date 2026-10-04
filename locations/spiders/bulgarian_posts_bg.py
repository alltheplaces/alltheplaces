import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class BulgarianPostsBGSpider(Spider):
    name = "bulgarian_posts_bg"
    item_attributes = {"brand": "Български пощи", "brand_wikidata": "Q2880826"}
    allowed_domains = ["bgpost.bg"]
    start_urls = ["https://bgpost.bg/api/offices?search_by_city_name_or_address="]

    async def start(self) -> AsyncIterator[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url)

    def parse(self, response):
        for location in response.json():
            location["street_address"] = location.pop("address", None)
            item = DictParser.parse(location)
            if "EMS" not in location["office_name"]:
                item["name"] = f"ПС {location['office_name']}"
                item["extras"]["official_name"] = f"Пощенска станция {location['office_name']}"
                item["extras"]["postal_code"] = location["postcode"]
            else:
                item["name"] = f"{location['office_name']}"
            item["city"] = location["city_name"]
            item["state"] = location["district"]
            item["phone"] = location["phone"]
            item["postcode"] = None
            apply_category(Categories.POST_OFFICE, item)

            has_break = False
            if location["note"] is not None:
                # Temporarily closed location, customers are redirected to the nearest post office
                # such closures typically last for months or years
                if "Временно преустановена дейност" in location["note"]:
                    item["opening_hours"] = f'off "{location["note"]}"'
                    yield item
                    continue
                if break_times := re.match(r"(\d+:\d+)-(\d+:\d+) - затворено", location["note"]):
                    break_start = break_times.group(1)
                    break_end = break_times.group(2)
                    has_break = True

            oh = OpeningHours()
            for day_name in DAYS_FULL:
                if location[f"working_hours_{day_name.lower()}"]:
                    try:
                        day_hours = location[f"working_hours_{day_name.lower()}"].split("-", 1)
                        if has_break and day_hours[0] < break_start < break_end < day_hours[1]:
                            oh.add_range(day_name, day_hours[0], break_start)
                            oh.add_range(day_name, break_end, day_hours[1])
                        else:
                            oh.add_range(day_name, day_hours[0], day_hours[1])
                    except ValueError:
                        continue
                else:
                    oh.set_closed(day_name)
            item["opening_hours"] = oh
            yield item
