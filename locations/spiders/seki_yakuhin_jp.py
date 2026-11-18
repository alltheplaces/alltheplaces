import re
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_JP, OpeningHours
from locations.items import Feature


class SekiYakuhinJPSpider(Spider):
    name = "seki_yakuhin_jp"
    item_attributes = {"brand": "セキ薬品", "brand_wikidata": "Q11314252"}
    start_urls = ["https://www.sekiyakuhin.co.jp/shop"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        shops = chompjs.parse_js_object(response.text[response.text.index("shops: [") + 7 :])
        for shop in shops:
            item = Feature()
            item["ref"] = shop["number"]
            item["branch"] = shop["name"]
            item["addr_full"] = shop["address"]
            if prefecture := re.match(r"^(東京都|北海道|(?:京都|大阪)府|.{2,3}県)", shop["address"]):
                item["state"] = prefecture.group(1)
            item["postcode"] = shop["zip"]
            item["phone"] = shop["tel"]
            item["extras"]["fax"] = shop["fax"]
            item["website"] = f"https://www.sekiyakuhin.co.jp/shop/info.php?i={shop['number']}"

            if coords := re.match(r"^\s*(-?\d+\.\d+)\s*[, ]\s*(-?\d+\.\d+)\s*$", shop["geolocation"] or ""):
                item["lat"], item["lon"] = coords.groups()

            if shop["shop_category_id"] == "3":
                item["name"] = "セキ薬局"
                apply_category(Categories.PHARMACY, item)
                apply_yes_no(Extras.DISPENSING, item, True)
            else:
                item["name"] = "ドラッグストアセキ"
                apply_category(Categories.SHOP_CHEMIST, item)

            item["opening_hours"] = self.parse_hours(shop["hours"], shop["comment"] or "")
            yield item

    @staticmethod
    def parse_times(text: str) -> list[tuple[str, str]] | None:
        times = re.findall(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", text)
        if not times or re.sub(r"\d{1,2}:\d{2}-\d{1,2}:\d{2}", "", text).strip():
            return None
        return times

    def parse_hours(self, hours: str, comment: str) -> OpeningHours | None:
        hours = hours.replace("〜", "-").replace("～", "-").replace("：", ":")
        base, _, special = hours.partition("※")
        if (times := self.parse_times(base)) is None:
            return None
        days = {day: times for day in DAYS}

        # Override for some days, e.g. "※木土9:00-14:00 15:00-19:00" or "※日祝 9:00-13:30 14:30-19:00"
        if special:
            match = re.fullmatch(r"\s*([月火水木金土日祝]+)\s*(.+)", special)
            if not match or (special_times := self.parse_times(match.group(2))) is None:
                return None
            for day in match.group(1):
                if day in DAYS_JP:
                    days[DAYS_JP[day]] = special_times

        # Closed days, e.g. "店休日：火曜・日曜・祝日". Public holidays are left out.
        if closed := re.search(r"店休日[：:]([^\s【<]*)", comment):
            for day in closed.group(1).split("・"):
                if day in ("祝日", "元日"):
                    continue
                if not re.fullmatch(r"[月火水木金土日]曜", day):
                    return None
                days.pop(DAYS_JP[day[0]], None)

        oh = OpeningHours()
        for day, ranges in days.items():
            for start, end in ranges:
                oh.add_range(day, start, end)
        return oh
