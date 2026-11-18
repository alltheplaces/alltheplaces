import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_WEEKDAY, OpeningHours

TIME_REGEX = re.compile(r"[0-2]\d:[0-5]\d")


class MosBurgerJPSpider(Spider):
    name = "mos_burger_jp"
    item_attributes = {
        "brand": "モスバーガー",
        "brand_wikidata": "Q1204169",
    }
    start_urls = ["https://www.mos.jp/data/shop/shop.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["shops"]:
            if "休業中" in store["name"] or "オープン予定" in store["name"]:
                continue

            item = DictParser.parse(store)
            item["name"] = "モスバーガー"
            item["ref"] = store["shop_cd"]
            item["website"] = f"https://www.mos.jp/shop/detail/?shop_cd={store['shop_cd']}"
            if store["tel1"] and store["tel2"] and store["tel3"]:
                item["phone"] = f"+81 {store['tel1']}-{store['tel2']}-{store['tel3']}"
            item["branch"] = store["name"].removeprefix("モスバーガー")
            item["extras"]["branch:ja-Hira"] = store["kana"].removeprefix("もすばーがー")
            item["postcode"] = f"{store['zip1']}-{store['zip2']}"
            item["extras"]["addr:province"] = store["pref_name"]
            item["addr_full"] = store["addr_all"]
            item["extras"]["start_date"] = store["openingday"]

            oh = OpeningHours()
            for days, key in ((DAYS_WEEKDAY, "wday"), (["Sa"], "sat"), (["Su"], "hol")):
                open_time, close_time = store[f"{key}_open"] or "", store[f"{key}_close"] or ""
                if TIME_REGEX.fullmatch(open_time) and TIME_REGEX.fullmatch(close_time):
                    oh.add_days_range(days, open_time, close_time)
            if oh.day_hours:
                item["opening_hours"] = oh

            apply_category(Categories.FAST_FOOD, item)

            yield item
