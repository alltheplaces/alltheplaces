import re
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.spiders.auchan_lu import MY_AUCHAN
from locations.spiders.auchan_pl import AuchanPLSpider


class AuchanROSpider(Spider):
    name = "auchan_ro"
    item_attributes = AuchanPLSpider.item_attributes
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Any]:
        yield JsonRequest(
            url="https://www.auchan.ro/api/dataentities/PU/search?_fields=address,city,clickAndCollectDrive,clickAndCollectStore,county,deliveryWithin24h,email,expressDelivery,fridaySchedule,holidaySchedule,latitude,longitude,mondaySchedule,myAuchanPetrom,phoneNumber,pickupFromDrive,saturdaySchedule,sellerId,storeName,sundaySchedule,thursdaySchedule,tuesdaySchedule,wednesdaySchedule,zipcode,id",
            headers={
                "REST-Range": "resources=0-500",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            store["street-address"] = store.pop("address", "")
            item = DictParser.parse(store)
            item["phone"] = item["phone"].replace("<br>", "; ")
            item["opening_hours"] = OpeningHours()
            for key in store:
                if "Schedule" in key:
                    day = key.split("Schedule")[0]
                    if day := sanitise_day(day):
                        for open_time, close_time in re.findall(r"(\d+:\d+)[-\s]+(\d+:\d+)", store[key]):
                            item["opening_hours"].add_range(day, open_time, close_time)
            item["website"] = f'https://www.auchan.ro/magazin/{store["id"]}'

            if item["name"].startswith("MyAuchan"):
                item["branch"] = item.pop("name").removeprefix("MyAuchan")
                item.update(MY_AUCHAN)
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif item["name"].startswith("ATAC HIPER DISCOUNT ") or item["name"].startswith("ATAC Hiper Discount "):
                item["branch"] = (
                    item.pop("name").removeprefix("ATAC HIPER DISCOUNT ").removeprefix("ATAC Hiper Discount ")
                )
                item["name"] = "ATAC"
                apply_category(Categories.SHOP_SUPERMARKET, item)
            elif item["name"].startswith("Auchan "):
                item["branch"] = item.pop("name").removeprefix("Auchan ")
                apply_category(Categories.SHOP_SUPERMARKET, item)

            yield item
