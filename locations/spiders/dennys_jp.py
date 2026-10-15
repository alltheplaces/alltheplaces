from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class DennysJPSpider(Spider):
    name = "dennys_jp"
    item_attributes = {"brand": "デニーズ", "brand_wikidata": "Q11320661"}
    days = dict(zip(DAYS, ["月", "火", "水", "木", "金", "土", "日"]))

    async def start(self) -> AsyncIterator[JsonRequest]:
        for points in [
            "w",
            "x",
            "z",
        ]:
            yield JsonRequest(url=f"https://shop.dennys.co.jp/api/point/{points}/")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["items"]:

            item = DictParser.parse(store)

            item["branch"] = item.pop("name").replace("デニーズ", "").split()[0]
            apply_category(Categories.RESTAURANT, item)

            item["opening_hours"] = OpeningHours()
            for index, day in enumerate(DAYS):
                ranges = [
                    hours.strip().split("-")
                    for hours in store["extra_fields"][f"{self.days[day]}曜日の営業時間"].split(",")
                ]
                for open_time, close_time in ranges:
                    # After-midnight hours are listed on the day the night started, so move them to the next day
                    overflow = len(ranges) > 1 and open_time in ("0:00", "00:00")
                    item["opening_hours"].add_range(DAYS[(index + overflow) % 7], open_time, close_time)
            item["website"] = f"https://shop.dennys.co.jp/map/{store['key']}/"
            item["phone"] = f"+81 {store['extra_fields']['電話番号']}"
            apply_yes_no("parking", item, store["extra_fields"]["駐車場あり"] == "1")
            apply_yes_no("toilets:wheelchair", item, store["extra_fields"]["だれでもトイレ"] == "1")
            apply_yes_no("changing_table", item, store["extra_fields"]["ベビーシート"] == "1")
            apply_yes_no("delivery", item, store["extra_fields"]["出前サービス"] == "1")
            apply_yes_no("elevator", item, store["extra_fields"]["エレベーター"] == "1")
            apply_yes_no("wheelchair", item, store["extra_fields"]["車椅子対応の入り口"] == "1")
            if store["extra_fields"]["コンセント"] == "1":
                item["extras"]["socket:nema_5_15"] = "yes"
            if store["extra_fields"]["全席禁煙"] == "1":
                item["extras"]["smoking"] = "no"
            item["postcode"] = store["extra_fields"]["郵便番号"]

            yield item
