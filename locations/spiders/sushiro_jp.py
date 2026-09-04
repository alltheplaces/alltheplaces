import json
import re
from collections.abc import AsyncIterator, Iterable

from scrapy.http import Request, Response

from locations.categories import Categories, Extras, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_JP, OpeningHours, day_range
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider

# Map of the site's "service" facility codes to OSM tags.
SERVICE_TAGS = {
    1: "parking",  # 駐車場あり
    2: "capacity:disabled",  # 身障者用駐車場
    3: "wheelchair",  # 1F店舗（スロープ有り）
    7: "changing_table",  # おむつ替えシート
}
# Facility codes deliberately not mapped to any OSM tag:
#   5 = 2階建て店舗 (storey count, no POI tag)
#   6 = エレベーター (no standard restaurant accessibility tag)
#   13 = 自動土産ロッカー (souvenir locker)
#   16 = デジロー (Sushiro digital-ordering system, brand-specific)
# Codes 4, 8, 9, 10, 11, 12, 14 are not rendered and meaning is unknown

# free-text 'memo' value
# example: "ご利用可能なクレジットカード： VISA・MasterCard・JCB・American Express・Diners Club・DISCOVER・銀聯"
CARD_BRANDS = {
    "VISA": PaymentMethods.VISA,
    "MasterCard": PaymentMethods.MASTER_CARD,
    "JCB": PaymentMethods.JCB,
    "American Express": PaymentMethods.AMERICAN_EXPRESS,
    "Diners Club": PaymentMethods.DINERS_CLUB,
    "DISCOVER": PaymentMethods.DISCOVER_CARD,
    "銀聯": PaymentMethods.UNIONPAY,
}

# JIS prefecture code used in <select name="pref"> options
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
)


class SushiroJPSpider(JSONBlobSpider):
    name = "sushiro_jp"
    item_attributes = {"brand": "スシロー", "brand_wikidata": "Q11257037"}
    start_urls = ["https://www.akindo-sushiro.co.jp/shop/"]

    async def start(self) -> AsyncIterator[Request]:
        # The store list is loaded per-prefecture via a ?pref=<id> query on the
        # same URL, and the prefecture ids are already hardcoded in PREFECTURES
        # (no need to scrape the start page's <select name="pref"> first).
        for pref_id, _ in PREFECTURES:
            yield Request(f"{self.start_urls[0]}?pref={pref_id}")

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
        # Recorded as tags (see each line for the source field):
        item["ref"] = feature["id"]
        item["branch"] = item.pop("name").splitlines()[0].strip()
        item["addr_full"] = feature["address"]
        item["postcode"] = f"{feature['zip1']}{feature['zip2']}"
        item["city"] = feature["city_name"]
        item["extras"]["addr:province"] = feature["pref_name"]
        item["country"] = "JP"
        item["opening_hours"] = self._parse_hours(feature["hours"])

        if fax := feature.get("fax"):
            item["extras"]["contact:fax"] = fax

        if kana := feature.get("kana"):
            item["extras"]["name:ja-Hira"] = kana

        if "クレジット" in (feature.get("memo") or ""):
            apply_yes_no(PaymentMethods.CREDIT_CARDS, item, True)
            for brand, tag in CARD_BRANDS.items():
                if brand in feature["memo"]:
                    apply_yes_no(tag, item, True)

        if line := feature.get("line_url"):
            item["extras"]["contact:line"] = line

        if line_mini := feature.get("line_mini_url"):
            apply_yes_no("reservation", item, True)
            item["extras"]["website:booking"] = line_mini

        for code, tag in SERVICE_TAGS.items():
            if any(int(s["service"]) == code for s in feature["service"]):
                if tag == "parking":
                    item["extras"]["parking"] = "yes"
                elif tag == "capacity:disabled":
                    apply_yes_no(Extras.PARKING_WHEELCHAIR, item, True)
                elif tag == "wheelchair":
                    apply_yes_no(Extras.WHEELCHAIR, item, True)
                elif tag == "changing_table":
                    apply_yes_no(Extras.BABY_CHANGING_TABLE, item, True)

        # Other skipped fields
        #   pref_id       JIS prefecture code
        #   city_id       internal
        #   base_post_id  internal (parent-store link)
        #   sushipass_id  internal membership-store id
        #   language      constant "0"
        #   category      constant "13"
        #   price_range   cost tier 1-7; no standard OSM tag
        #   access        transport directions; no standard OSM key
        #   result_name   duplicate of name plus a price note
        #   togo_menu_url / demaecan_url / uber_eats_url
        #                 takeout/delivery links, empty for most stores
        #   recruit_url   job/hiring page, not POI data
        #   status        constant "0" (open)
        #   output_flag   constant "1" (shown on site)
        #   created / modified / start_datetime / end_datetime / open_datetime / close_datetime
        #   / renewal_start_datetime / renewalend_datetime
        #                 CMS / schedule metadata; closure windows are not
        #                 reliably populated and are surfaced instead in the
        #                 name/hours text of affected stores

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "sushi"

        yield item

    @staticmethod
    def _expand_days(raw_day_part: str) -> list[str]:
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

    @staticmethod
    def _parse_hours(text: str) -> str:
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
            for day in SushiroJPSpider._expand_days(line[: time_match.start()]):
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
