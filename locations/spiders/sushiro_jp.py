import json
import re
from typing import Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_JP, OpeningHours, day_range
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

# Prefecture ids used by the site's <select name="pref"> store locator, keyed
# by the JIS prefecture code each option carries. Used to build the
# per-prefecture ?pref=<id> requests that return every store in that
# prefecture.
PREFECTURES = (
    (1, "北海道"),
    (2, "青森県"),
    (3, "岩手県"),
    (4, "宮城県"),
    (5, "秋田県"),
    (6, "山形県"),
    (7, "福島県"),
    (8, "茨城県"),
    (9, "栃木県"),
    (10, "群馬県"),
    (11, "埼玉県"),
    (12, "千葉県"),
    (13, "東京都"),
    (14, "神奈川県"),
    (15, "新潟県"),
    (16, "富山県"),
    (17, "石川県"),
    (18, "福井県"),
    (19, "山梨県"),
    (20, "長野県"),
    (21, "岐阜県"),
    (22, "静岡県"),
    (23, "愛知県"),
    (24, "三重県"),
    (25, "滋賀県"),
    (26, "京都府"),
    (27, "大阪府"),
    (28, "兵庫県"),
    (29, "奈良県"),
    (30, "和歌山県"),
    (31, "鳥取県"),
    (32, "島根県"),
    (33, "岡山県"),
    (34, "広島県"),
    (35, "山口県"),
    (36, "徳島県"),
    (37, "香川県"),
    (38, "愛媛県"),
    (39, "高知県"),
    (40, "福岡県"),
    (41, "佐賀県"),
    (42, "長崎県"),
    (43, "熊本県"),
    (44, "大分県"),
    (45, "宮崎県"),
    (46, "鹿児島県"),
    (47, "沖縄県"),
)  # fmt: skip


def expand_days(raw_day_part: str) -> list[str]:
    stripped = raw_day_part.replace("祝", "").strip()
    if not stripped:
        return list(DAYS)
    if "-" in stripped:
        start_part, _, end_part = stripped.partition("-")
        start = DAYS_JP.get(start_part[-1]) if start_part else None
        end = DAYS_JP.get(end_part[-1]) if end_part else None
        if start and end:
            return day_range(start, end)
        return []
    return [DAYS_JP[c] for c in stripped if c in DAYS_JP]


def parse_hours(text: str) -> str:
    oh = OpeningHours()
    has_holiday = False
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("※"):
            continue
        has_holiday = has_holiday or "祝" in line
        line = line.replace("～", "-").replace("〜", "-").replace("：", ":")
        time_match = re.search(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})", line)
        if not time_match:
            continue
        open_time, close_time = time_match.group(1), time_match.group(2)
        for day in expand_days(line[: time_match.start()]):
            oh.add_range(day, open_time, close_time)

    result = oh.as_opening_hours()
    if not has_holiday or not result:
        return result

    # The OpeningHours helper has no concept of public holidays, so append
    # PH to the weekend group (土日祝) manually rather than drop it.
    groups = result.split("; ")
    for index, group in enumerate(groups):
        day_part, _, hours = group.partition(" ")
        if "Sa" in day_part or "Su" in day_part:
            groups[index] = f"{day_part},PH {hours}"
            break
    return "; ".join(groups)


class SushiroJPSpider(JSONBlobSpider):
    name = "sushiro_jp"
    item_attributes = {"brand": "スシロー", "brand_wikidata": "Q11257037"}
    start_urls = ["https://www.akindo-sushiro.co.jp/shop/"]

    def parse(self, response: Response) -> Iterable[Feature | Request]:
        if "?pref=" not in response.url:
            for pref_id, _ in PREFECTURES:
                yield Request(f"{self.start_urls[0]}?pref={pref_id}")
            return
        yield from super().parse(response)

    def extract_json(self, response: Response) -> list[dict]:
        data_raw = response.xpath("//script[contains(text(), 'items = [')]/text()").get()
        start = data_raw.rindex("items = [") + len("items = [")
        depth = 1
        i = start
        while depth > 0:
            char = data_raw[i]
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
            i += 1
        return json.loads(data_raw[start - 1 : i])

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["id"]
        item["branch"] = item.pop("name").splitlines()[0].strip()
        item["addr_full"] = feature["address"]
        item["postcode"] = f'{feature["zip1"]}{feature["zip2"]}'
        item["city"] = feature["city_name"]
        item["state"] = feature["pref_name"]
        item["country"] = "JP"
        item["opening_hours"] = parse_hours(feature["hours"])

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sushi"

        yield item
