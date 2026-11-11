from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, DAYS_FULL, OpeningHours


class AedJPSpider(Spider):
    name = "aed_jp"
    custom_settings = {"DOWNLOAD_TIMEOUT": 60}

    def make_request(self, rank: str, page: int, limit: int = 200) -> JsonRequest:
        return JsonRequest(
            url=f"https://www.qqzaidanmap.jp/api/aed/list?aed[install_prefecture_id]=&aed[install_address]=&aed[install_location_name]=&aed[rank]={rank}&limit={limit}&aed[install_type_id][]=&page={page}",
            cb_kwargs=dict(rank=rank, page=page),
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        for rank in ["A", "B", "C", "D"]:
            yield self.make_request(rank, 1)

    def parse(self, response: Response, rank: str, page: int) -> Any:
        for aed in response.json()["aeds"]:
            item = DictParser.parse(aed)
            item["ref"] = aed["id"]
            item["lat"] = aed["location"]["latitude"]
            item["lon"] = aed["location"]["longitude"]
            item["website"] = (
                f"https://www.qqzaidanmap.jp/map/my_map?latitude={item['lat']}&longitude={item['lon']}&zoom=16&id={aed['id']}"
            )
            apply_category(Categories.DEFIBRILLATOR, item)
            item["extras"]["defibrillator:location"] = aed["install_address_detail"]
            item["street_address"] = aed["install_address"]
            item["extras"]["addr:province"] = aed["install_prefecture_name"]
            item["name"] = aed["install_location_name"]

            if aed["utility_time_type"] == 1:
                times = ("00:00", "23:59")
            elif (
                aed["utility_time_from"]
                and aed["utility_time_to"]
                and aed["utility_time_from"] != aed["utility_time_to"]
            ):
                times = (aed["utility_time_from"][11:16], aed["utility_time_to"][11:16])
            else:
                times = None
            closed = [day for day, day_name in zip(DAYS, DAYS_FULL) if aed[f"closed_on_{day_name.lower()}s"]]
            # Devices closed every day are only usable during events or term times described in free text.
            if times and len(closed) < 7:
                oh = OpeningHours()
                for day in DAYS:
                    if day in closed:
                        oh.set_closed(day)
                    else:
                        oh.add_range(day, *times)
                item["opening_hours"] = oh

            if aed["everyone_allow"] == "認める":
                item["extras"]["access"] = "yes"
            elif aed["everyone_allow"] == "認めない":
                item["extras"]["access"] = "private"

            yield item

        if page < response.json()["pages"]["total_pages"]:
            yield self.make_request(rank, page + 1)
