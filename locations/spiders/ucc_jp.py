import json
import re
from typing import Iterable

from locations.categories import Categories, Extras, PaymentMethods, Sells, apply_category, apply_yes_no
from locations.hours import DAYS_JP, DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours, day_range
from locations.items import Feature
from locations.storefinders.location_cloud import LocationCloudSpider

# delivery partners: (display name, Wikidata QID or None)
DELIVERY_PARTNERS = {
    "出前館": ("出前館", "Q11395551"),
    "Rocket Now": ("Rocket Now", None),
    "Uber Eats": ("Uber Eats", "Q21462723"),
}


class UccJPSpider(LocationCloudSpider):
    name = "ucc_jp"
    api_endpoint = "https://shop.ufs.co.jp/ufs/api/proxy2/shop/list"
    website_formatter = "https://shop.ufs.co.jp/ufs/spot/detail?code={}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:

        if "kaigai" in source_feature["code"]:
            return  # remove overseas locations with fake coordinates

        if not source_feature.get("categories"):
            return

        match source_feature["categories"][0]["code"]:
            case "01":
                item["brand"] = "上島珈琲店"
                item["brand_wikidata"] = "Q96152143"
                item["branch"] = source_feature["name"].removeprefix("上島珈琲店　")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby.removeprefix("UESHIMA COFFEE ")
                apply_category(Categories.COFFEE_SHOP, item)
            case "04" | "05" | "08" | "09" | "16":
                item["brand"] = source_feature["categories"][0]["name"]
                item["branch"] = source_feature.get("name")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby
                apply_category(Categories.COFFEE_SHOP, item)
            case "11" | "12":
                item["brand"] = source_feature["categories"][0]["name"]
                item["branch"] = source_feature.get("name")
                if ruby := source_feature.get("ruby"):
                    item["extras"]["branch:ja-Hira"] = ruby
                apply_category(Categories.SHOP_COFFEE, item)
            case _:
                return

        yield item

    def parse_detail_page(self, response, item: Feature, source_feature: dict) -> Iterable[Feature]:
        start = response.text.index("spotDetail = ") + len("spotDetail = ")
        detail = json.JSONDecoder().raw_decode(response.text, start)[0]

        flags = {}
        for col in detail["detailColumns"]:
            for flag in col.get("columns", {}).get("flag", []):
                flags[flag["label"]] = flag["value"] == "true"

        # Brewing methods (ペーパードリップ/ネルドリップ → filter coffee; エスプレッソ → espresso; コールドブリュー → cold brew)
        if flags.get("ペーパードリップ") or flags.get("ネルドリップ"):
            apply_yes_no("drink:filter_coffee", item, True)
        if flags.get("エスプレッソ"):
            apply_yes_no("drink:espresso", item, True)
        if flags.get("コールドブリュー"):
            apply_yes_no("drink:cold_brew", item, True)

        # Facilities
        if flags.get("全席禁煙"):
            item["extras"]["smoking"] = "no"
        if flags.get("専用駐車場有"):
            item["extras"]["parking"] = "yes"
        apply_yes_no("socket:nema_1_15", item, flags.get("コンセント席有", False))
        apply_yes_no(Extras.WIFI, item, flags.get("Wi-Fi フリー", False))
        if flags.get("Wi-Fi フリー"):
            item["extras"]["internet_access:fee"] = "no"

        # Delivery
        partners = [v for k, v in DELIVERY_PARTNERS.items() if flags.get(k)]
        if partners:
            apply_yes_no(Extras.DELIVERY, item, True)
            item["extras"]["delivery:partner"] = ";".join(name for name, _ in partners)
            wikidata = [qid for _, qid in partners if qid]
            if wikidata:
                item["extras"]["delivery:partner:wikidata"] = ";".join(wikidata)

        # Payment
        apply_yes_no(PaymentMethods.ICSF, item, flags.get("交通系電子マネー", False))

        # Menu / offerings
        if flags.get("モーニングメニュー"):
            apply_yes_no(Extras.BREAKFAST, item, True)
        if flags.get("カフェインレスコーヒー"):
            item["extras"]["drink:coffee:decaf"] = "yes"
        if flags.get("アルコールメニュー"):
            apply_yes_no(Sells.ALCOHOL, item, True)
        if flags.get("キッズメニュー"):
            item["extras"]["child"] = "yes"
        apply_yes_no(Extras.TAKEAWAY, item, flags.get("テイクアウト可", False))

        # Opening hours
        default_col = next((c for c in detail["detailColumns"] if c.get("code") == "default"), None)
        if default_col:
            for t in default_col.get("columns", {}).get("text", []):
                if t["label"] == "営業時間":
                    item["opening_hours"] = self._parse_hours(t["value"])
                    break

        yield item

    @staticmethod
    def _parse_hours(text: str) -> OpeningHours | None:
        # Strip HTML tags, parenthetical remarks, and trailing notes after ※
        s = re.sub(r"<[^>]+>", " ", text)
        s = re.sub(r"（[^）]*）|\([^)]*\)", "", s)
        s = re.sub(r"※.*", "", s)
        s = s.replace("～", "-").replace("〜", "-").replace("：", ":").replace("／", "/").replace("~", "-")

        # Normalise the rare "平日 / HH:MM" pattern (slash used as day/time separator)
        # e.g. "平日 / 9:00-19:00   土日祝 / 8:00-20:00" → "平日 9:00-19:00 / 土日祝 8:00-20:00"
        s = re.sub(r"(平日|土日祝?|日祝?|土)\s*/\s*(\d)", r"\1 \2", s)

        oh = OpeningHours()
        # Track which OSM day groups (Sa, Su) need PH appended
        ph_days: set[str] = set()
        pending_day = None

        for part in re.split(r"\s*/\s*", s):
            part = part.strip()
            if not part:
                continue

            # Find all time ranges in this segment, tracking text between them for day labels.
            # e.g. "平日 9:00-19:00   土日祝 8:00-20:00" → two ranges with day prefixes.
            pos = 0
            found_time = False
            for m in re.finditer(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", part):
                found_time = True
                open_time, close_time = m.group(1), m.group(2)
                day_prefix = part[pos : m.start()].strip().rstrip(":").strip()
                day_part = day_prefix or pending_day or ""
                pending_day = None
                pos = m.end()

                if not day_part or day_part in ("毎日", "全日"):
                    days = DAYS_WEEKDAY + DAYS_WEEKEND
                elif "平日" in day_part:
                    days = DAYS_WEEKDAY
                elif re.search(r"[月火水木金土日]", day_part):
                    days = UccJPSpider._expand_kanji_days(day_part)
                else:
                    days = []

                if "祝" in day_part:
                    ph_days.update(d for d in days if d in ("Sa", "Su"))

                for day in days:
                    oh.add_range(day, open_time, close_time)

            # If the segment had no time range, it may be a dangling day label
            if not found_time and re.search(r"[平土日祝月火水木金]", part):
                pending_day = part.strip()

        result = oh.as_opening_hours()
        if not result:
            return None

        # Append PH to the groups for days that had 祝 in their source day_part
        if ph_days:
            groups = result.split("; ")
            for i, group in enumerate(groups):
                day_part, _, hours = group.partition(" ")
                if any(d in day_part for d in ph_days):
                    groups[i] = f"{day_part},PH {hours}"
            result = "; ".join(groups)

        return result

    @staticmethod
    def _expand_kanji_days(day_part: str) -> list[str]:
        days = []
        # Handle comma/middle-dot separated groups, e.g. "月・水・金" or "月,水"
        for segment in re.split(r"[・,]", day_part):
            segment = segment.strip()
            if not segment:
                continue
            # Range: "月-木" → Mo..Th
            if "-" in segment:
                start_char, _, end_char = segment.partition("-")
                start = DAYS_JP.get(start_char.strip())
                end = DAYS_JP.get(end_char.strip())
                if start and end:
                    days.extend(day_range(start, end))
            elif segment in DAYS_JP:
                days.append(DAYS_JP[segment])
            else:
                # multi-char like "土日" or "日祝"
                for ch in segment:
                    if ch in DAYS_JP:
                        days.append(DAYS_JP[ch])
        return days
