import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_JP, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature
from locations.storefinders.area_marker import AreaMarkerSpider

# Open days as free text, used when the hours text has no day prefix of its own.
OPEN_DAYS = {
    "年中無休": DAYS,
    "月～金曜日": DAYS_WEEKDAY,
    "月～土曜日": DAYS_WEEKDAY + ["Sa"],
    "平日・土曜日": DAYS_WEEKDAY + ["Sa"],
    "日曜のみ休み": ["Mo", "Tu", "We", "Th", "Fr", "Sa"],
    "土曜のみ休み": ["Mo", "Tu", "We", "Th", "Fr", "Su"],
    "土日のみ休み": DAYS_WEEKDAY,
    "祝日のみ休み": DAYS,
}

# e.g. "平日07:00～19:00 土/日/祝08:00～19:00" or "24時間", as day spec / time range pairs.
SEGMENT_RE = re.compile(r"([^0-9\s]*?)\s*(24時間|\d{1,2}:\d{2}\s*[～~]\s*\d{1,2}:\d{2})")


def parse_days(spec: str) -> list[str]:
    # Public holidays (祝) are skipped: OpeningHours can't express them.
    days = []
    for token in re.split(r"[/／・]", spec.replace("曜", "")):
        if token == "平日":
            days += DAYS_WEEKDAY
        elif "～" in token:
            start, _, end = token.partition("～")
            days += DAYS[DAYS.index(DAYS_JP[start]) : DAYS.index(DAYS_JP[end]) + 1]
        elif token in DAYS_JP:
            days.append(DAYS_JP[token])
    return days


class LawsonBankJPSpider(AreaMarkerSpider):
    name = "lawson_bank_jp"
    item_attributes = {"brand": "ローソン銀行", "brand_wikidata": "Q11350963"}
    corp_id = "lbankatm"
    referer = "https://maps.lawsonbank.jp/lbankatm/map"
    fields = {
        "ref": "kyo_id",  # ATM id
        "name": "name",  # "ローソン銀行ATM　<branch>共同出張所"
        "lat": "lat_en",  # latitude (WGS84. lat_jp/lon_jp are in the Tokyo datum)
        "lon": "lon_en",  # longitude (WGS84)
        "addr": "addr_1",
        "postcode": "zip_code",
        "days": "col_5",  # open days, as free text
        "open_hours": "col_6",  # day-scoped opening times, followed by a note
    }

    def post_process_item(
        self, item: Feature, response: TextResponse, store: dict, raw_record: dict, **kwargs
    ) -> Iterable[Feature]:
        item["name"] = "ローソン銀行"
        item["branch"] = (
            store["name"].removeprefix("ローソン銀行ＡＴＭ").removeprefix("ローソン銀行ATM").removesuffix("共同出張所")
        )
        item["website"] = f"https://maps.lawsonbank.jp/lbankatm/info/{store['ref']}"

        oh = OpeningHours()
        for day_spec, times in SEGMENT_RE.findall(store["open_hours"]):
            opens, _, closes = times.replace("~", "～").partition("～")
            if not closes:  # "24時間"
                opens, closes = "00:00", "24:00"
            elif opens == closes:  # "00:00～00:00"
                closes = "24:00"
            days = parse_days(day_spec) if day_spec else OPEN_DAYS[store["days"]]
            if days:
                oh.add_days_range(days, opens, closes)
        item["opening_hours"] = oh

        apply_category(Categories.ATM, item)
        yield item
