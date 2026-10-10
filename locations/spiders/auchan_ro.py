import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.spiders.auchan_lu import AUCHAN, MY_AUCHAN

HOTLINE = "021-9141"


class AuchanROSpider(Spider):
    name = "auchan_ro"
    item_attributes = AUCHAN

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://www.auchan.ro/api/dataentities/PU/search?_fields=address,city,county,email,fridaySchedule,holidaySchedule,latitude,longitude,mondaySchedule,phoneNumber,saturdaySchedule,storeName,sundaySchedule,thursdaySchedule,tuesdaySchedule,wednesdaySchedule,zipcode,id",
            headers={
                "REST-Range": "resources=0-500",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            location["street-address"] = location.pop("address", "")
            item = DictParser.parse(location)

            item["email"] = None
            numbers = [number.strip() for number in (item["phone"] or "").split("<br>")]
            item["phone"] = "; ".join(number for number in numbers if number and number != HOTLINE) or None

            item["opening_hours"] = OpeningHours()
            for key in location:
                if "Schedule" in key:
                    day = key.split("Schedule")[0]
                    if day := sanitise_day(day):
                        for open_time, close_time in re.findall(r"(\d+:\d+)[-\s]+(\d+:\d+)", location[key] or ""):
                            item["opening_hours"].add_range(day, open_time, close_time)

            item["website"] = f'https://www.auchan.ro/magazin/{location["id"]}'

            store_name = item.pop("name", "") or ""
            if store_name.startswith("MyAuchan"):
                item["branch"] = store_name.removeprefix("MyAuchan").strip() or None
                item.update(MY_AUCHAN)
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif store_name.upper().startswith("ATAC "):
                item["name"] = "ATAC"
                item["branch"] = re.sub(r"^ATAC (?:HIPER|SUPER) DISCOUNT ", "", store_name, flags=re.IGNORECASE)
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif store_name.startswith("Auchan "):
                item["branch"] = store_name.removeprefix("Auchan ")
                apply_category(Categories.SHOP_SUPERMARKET, item)
            else:
                item["name"] = store_name
                self.crawler.stats.inc_value(f"atp/{self.name}/unknown_store_name/{store_name}")

            yield item
