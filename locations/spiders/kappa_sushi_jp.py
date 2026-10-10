import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.google_url import url_to_coords
from locations.hours import DAYS, DAYS_JP, OpeningHours, day_range
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.lang_utils import katakana_to_hiragana

_DAY_KANJI = re.compile(r"[月火水木金土日]")


class KappaSushiJPSpider(JSONBlobSpider):
    name = "kappa_sushi_jp"
    item_attributes = {"brand": "かっぱ寿司", "brand_wikidata": "Q11263916"}
    start_urls = ["https://www.kappasushi.jp/master_data/json/shoplist.json"]
    locations_key = "Store"

    def post_process_item(self, item: Feature, response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["code"]
        item["branch"] = item.pop("name", "").split("※")[0].strip()
        item["street_address"] = item.pop("addr_full", "")

        if feature["code"] == "0552":
            # DB has a bad lat/lon (lat == lon). Correct only this coords in map_url
            # since the map's lat/lon is slightly different from the DB lat/lon
            item["lat"], item["lon"] = url_to_coords(feature["map_url"])

        if kana := feature.get("name_kana"):
            item["extras"]["branch:ja-Hira"] = katakana_to_hiragana(kana)
        if seats := feature.get("seats"):
            item["extras"]["capacity"] = seats
        item["opening_hours"] = self._parse_hours(feature["open_time"])

        apply_category(Categories.FAST_FOOD, item)

        yield item

    @staticmethod
    def _parse_hours(text: str) -> str:
        oh = OpeningHours()
        has_holiday = False
        for line in text.split("<br>"):
            line = line.strip()
            if not line or line.startswith("※") or "最終入店" in line or "閉店" in line:
                continue
            has_holiday = has_holiday or "祝" in line

            # Find where the time part begins (first 午前/午後 marker).
            time_start = min((i for m in ("午前", "午後") if (i := line.find(m)) != -1), default=None)
            if time_start is None:
                continue
            day_part = line[:time_start].replace("～", "-")
            time_part = line[time_start:]

            m = re.search(
                r"(午前|午後)?(\d{1,2}):(\d{2})\s*[～〜~-]\s*(午前|午後)?(\d{1,2}):(\d{2})",
                time_part,
            )
            if not m:
                continue
            open_time = KappaSushiJPSpider._convert_time(m.group(2), m.group(3), m.group(1))
            close_time = KappaSushiJPSpider._convert_time(m.group(5), m.group(6), m.group(4) or "午前")

            for day in KappaSushiJPSpider._expand_days(day_part):
                oh.add_range(day, open_time, close_time)

        result = oh.as_opening_hours()
        if not has_holiday or not result:
            return result

        # OpeningHours has no concept of public holidays, so append PH to the
        # weekend group (土日祝) rather than drop it.
        groups = result.split("; ")
        for index, group in enumerate(groups):
            day_part, _, hours = group.partition(" ")
            if "Sa" in day_part or "Su" in day_part:
                groups[index] = f"{day_part},PH {hours}"
                break
        return "; ".join(groups)

    @staticmethod
    def _convert_time(hh: str, mm: str, marker: str) -> str:
        hour = int(hh)
        if marker == "午後" and hour < 12:
            hour += 12
        return f"{hour:02d}:{mm}"

    @staticmethod
    def _expand_days(raw_day_part: str) -> list[str]:
        part = raw_day_part.replace("祝", "").strip()
        if not part:
            return list(DAYS)
        if "-" in part:
            start_token, _, end_token = part.partition("-")
            start = DAYS_JP[KappaSushiJPSpider._day_token(start_token)]
            end = DAYS_JP[KappaSushiJPSpider._day_token(end_token)]
            return day_range(start, end)
        return [DAYS_JP[token] for token in _DAY_KANJI.findall(part)]

    @staticmethod
    def _day_token(token: str) -> str:
        # 月曜 -> 月 ; 月曜日 -> 月 ; 月 -> 月 ; 日曜日 -> 日
        return token.removesuffix("曜日").removesuffix("曜")
