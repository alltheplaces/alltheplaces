import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_JP, DAYS_WEEKDAY, OpeningHours, day_range
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider


class OriginToshuSpider(LocationCloudSpider):
    name = "origin_toshu"
    api_endpoint = "https://shop.toshu.co.jp/toshu/api/proxy2/shop/list"
    website_formatter = "https://shop.toshu.co.jp/toshu/spot/detail?code={}"

    def parse_detail_page(self, response: Response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        flags = {flag["label"]: flag["value"] == "true" for flag in detail["flags"].values()}
        apply_yes_no(Extras.TAKEAWAY, item, flags["テイクアウト"])
        apply_yes_no(Extras.INDOOR_SEATING, item, flags["イートイン"])
        apply_yes_no(Extras.DELIVERY, item, flags["デリバリー"])
        apply_yes_no(Extras.PARKING, item, flags["駐車場"])
        apply_yes_no("socket:nema_1_15", item, flags.get("コンセント", False))

        for column in detail["detailColumns"]:
            for text in column["columns"].get("text", []):
                if text["code"] == "00004":
                    item["opening_hours"] = self.parse_hours(text["value"])
        yield item

    @staticmethod
    def parse_hours(value: str) -> OpeningHours | None:
        # e.g. "6:00～22:00<br>弁当等の注文は21:45までとなっております。", "24時間営業",
        # "10:30～22:00<br>（ラストオーダー21:45）<br>【土日祝】<br>11:00～22:30<br>（ラストオーダー22:15）"
        oh = OpeningHours()
        if value.startswith("24時間営業"):
            if value.partition("<br>")[0] != "24時間営業":
                return None  # e.g. "24時間営業（土日祝6:00～22:00）※日祝明けの平日は6:00オープン"
            oh.add_days_range(DAYS, "00:00", "23:59")
            return oh

        closed = [DAYS_JP[day] for day in re.findall(r"([月火水木金土日])曜日は定休日", value)]
        value = re.sub(r"[（(]ラストオーダー.*?[）)]", "", value)
        # drop notes such as last orders and bento ordering times, keep day labels on their own line
        lines = [
            line for line in re.split(r"<br>|\n", value) if not re.search(r"注文|ラストオーダー|イートイン|※", line)
        ]
        value = re.sub(r"[【】（）()]", " ", " ".join(lines))
        pattern = r"([平月火水木金土日祝曜・～]*)\s*(\d{1,2}:\d{2})\s*[～~-]\s*(\d{1,2}:\d{2})"
        if re.search(r"[月火水木金土日祝]", re.sub(pattern, "", value)):
            return None  # e.g. "土日祝は22:00まで"

        default, by_day = [], {}
        for label, open_time, close_time in re.findall(pattern, value):
            if not label:
                default.append((open_time, close_time))
                continue
            days = list(DAYS_WEEKDAY) if "平日" in label else []
            label = re.sub(r"平日|祝日|祝|曜|・", "", label)
            if m := re.fullmatch(r"([月火水木金土日])～([月火水木金土日])", label):
                days += day_range(DAYS_JP[m.group(1)], DAYS_JP[m.group(2)])
            else:
                days += [DAYS_JP[day] for day in label]
            for day in days:
                by_day.setdefault(day, []).append((open_time, close_time))

        if not default and not by_day:
            return None
        for day in DAYS:
            if day in closed:
                oh.set_closed(day)
                continue
            for open_time, close_time in by_day.get(day, default):
                oh.add_range(day, open_time, close_time)
        return oh

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["phone"] = source_feature["phone"]
        name = source_feature.get("name") or ""
        match source_feature["categories"][0]["name"]:
            case "キッチンオリジン":
                item["brand_wikidata"] = "Q92658990"
                item["branch"] = name.removeprefix("キッチンオリジン ") or None
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("きっちんおりじん ")
                apply_category(Categories.FAST_FOOD, item)
            case "れんげ食堂Toshu":
                item["brand_wikidata"] = "Q92662226"
                item["branch"] = name.removeprefix("れんげ食堂Toshu ") or None
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("れんげしょくどうとうしゅう ")
                apply_category(Categories.RESTAURANT, item)
            case "オリジンデリカ":
                item["brand"] = "オリジンデリカ"
                item["branch"] = name.removeprefix("オリジンデリカ ") or None
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("おりじんでりか ")
                apply_category(Categories.FAST_FOOD, item)
            case "オリジン弁当":
                item["brand_wikidata"] = "Q11292632"
                item["branch"] = name.removeprefix("オリジン弁当 ") or None
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("おりじんべんとう ")
                apply_category(Categories.FAST_FOOD, item)
            case _:
                item["brand"] = source_feature["categories"][0]["name"]
                item["branch"] = name or None
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby
                apply_category(Categories.RESTAURANT, item)

        yield item
