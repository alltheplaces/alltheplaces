import re
from typing import Any, AsyncIterator, Iterable

import scrapy
from scrapy.http import FormRequest, Response

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# The 47 prefectures the store finder's free-text "address" search
# understands. Searching by prefecture (rather than a lat/lng radius) keeps
# every store within the searched prefecture, and each prefecture query
# stays well under the API's page-size cap once paginated with "morelist"
# (see parse_prefecture below).
PREFECTURES = [
    "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
    "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
    "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
    "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
    "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
    "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
    "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
]  # fmt: skip

DAY_CHARS = {"月": "Mo", "火": "Tu", "水": "We", "木": "Th", "金": "Fr", "土": "Sa", "日": "Su"}
HOURS_RE = re.compile(r"([月火水木金土日祝平、\-]*)\s*(\d{1,2}:\d{2})-(\d{1,2}:\d{2})")


def expand_days(raw_day_part: str) -> list[str] | None:
    stripped = raw_day_part.replace("祝", "").replace("、", "").strip()
    if not stripped:
        return list(DAYS)
    if "平日" in stripped:
        return ["Mo", "Tu", "We", "Th", "Fr"]
    if "-" in stripped:
        start_part, _, end_part = stripped.partition("-")
        start = DAY_CHARS.get(start_part[-1]) if start_part else None
        end = DAY_CHARS.get(end_part[-1]) if end_part else None
        if not start or not end:
            return None
        start_index, end_index = DAYS.index(start), DAYS.index(end)
        if start_index <= end_index:
            return DAYS[start_index : end_index + 1]
        return DAYS[start_index:] + DAYS[: end_index + 1]
    days = [DAY_CHARS[c] for c in stripped if c in DAY_CHARS]
    return days or None


def normalise_time(value: str) -> str:
    # A handful of records use hours like "24:30" for 00:30 the next day
    # instead of the "翌" (next day) marker used elsewhere.
    hour, _, minute = value.partition(":")
    return f"{int(hour) % 24:02d}:{minute}"


def parse_hours(*parts: str) -> OpeningHours | None:
    text = " ".join(p for p in parts if p)
    if not text.strip():
        return None
    if "24時間" in text:
        oh = OpeningHours()
        for day in DAYS:
            oh.add_range(day, "00:00", "23:59")
        return oh

    # Non-hours annotations (e.g. "※ラストオーダーは閉店の30分前です。", labels
    # like "■店内") don't match HOURS_RE below and are harmlessly skipped.
    text = text.replace("翌", "").replace("〜", "-").replace("～", "-").replace("~", "-")

    oh = OpeningHours()
    found = False
    for day_part, open_time, close_time in HOURS_RE.findall(text):
        days = expand_days(day_part)
        if not days:
            continue
        open_time, close_time = normalise_time(open_time), normalise_time(close_time)
        for day in days:
            oh.add_range(day, open_time, close_time)
        found = True

    return oh if found else None


class ZenshoJPSpider(scrapy.Spider):
    name = "zensho_jp"
    allowed_domains = ["maps.zensho.co.jp"]

    # Keyed by the Japanese brand name returned in the API's "mapdata".
    # NSI brand strings/wikidata used where a brand has an NSI entry; the
    # issue's own notes on which brands lack a Wikidata item were verified
    # against wikidata.org (and one supplied ID, for Tenkaichi, turned out to
    # actually identify the unrelated Tenkaippin ramen chain and is omitted).
    BRANDS = {
        "すき家": {
            "brand": "すき家",
            "brand_wikidata": "Q6137375",
            "category": Categories.FAST_FOOD,
            "cuisine": "beef_bowl",
        },
        "なか卯": {
            "brand": "なか卯",
            "brand_wikidata": "Q11274132",
            "category": Categories.FAST_FOOD,
            "cuisine": "udon",
        },
        "ゼッテリア": {
            "brand": "ゼッテリア",
            "brand_wikidata": "Q136796344",
            "category": Categories.FAST_FOOD,
            "cuisine": "burger",
        },
        "はま寿司": {
            "brand": "はま寿司",
            "brand_wikidata": "Q17220385",
            "category": Categories.FAST_FOOD,
            "cuisine": "sushi",
        },
        "ココス": {
            "brand": "ココス",
            "brand_wikidata": "Q11301951",
            "category": Categories.RESTAURANT,
            "cuisine": "western;japanese",
        },
        "エルトリート": {
            "brand": "エルトリート",
            "brand_wikidata": None,
            "category": Categories.RESTAURANT,
            "cuisine": "mexican",
        },
        "ビッグボーイ": {
            "brand": "ビッグボーイ",
            "brand_wikidata": "Q4386779",
            "category": Categories.RESTAURANT,
            "cuisine": "western;japanese",
        },
        "ヴィクトリアステーション": {
            "brand": "ヴィクトリアステーション",
            "brand_wikidata": "Q11351997",
            "category": Categories.RESTAURANT,
            "cuisine": "steak_house",
        },
        "ジョリーパスタ": {
            "brand": "ジョリーパスタ",
            "brand_wikidata": "Q10852718",
            "category": Categories.RESTAURANT,
            "cuisine": "pasta",
        },
        "華屋与兵衛": {
            "brand": "華屋与兵衛",
            "brand_wikidata": "Q11620063",
            "category": Categories.RESTAURANT,
            "cuisine": "japanese",
        },
        "オリーブの丘": {
            "brand": "オリーブの丘",
            "brand_wikidata": "Q113654309",
            "category": Categories.RESTAURANT,
            "cuisine": "italian",
        },
        "かつ庵": {
            "brand": "かつ庵",
            "brand_wikidata": None,
            "category": Categories.RESTAURANT,
            "cuisine": "japanese;tonkatsu",
        },
        "熟成焼肉いちばん": {
            "brand": "熟成焼肉いちばん",
            "brand_wikidata": None,
            "category": Categories.RESTAURANT,
            "cuisine": "yakiniku",
        },
        "伝丸": {"brand": "伝丸", "brand_wikidata": None, "category": Categories.RESTAURANT, "cuisine": "ramen"},
        "壱鵠堂": {"brand": "壱鵠堂", "brand_wikidata": None, "category": Categories.RESTAURANT, "cuisine": "ramen"},
        "威風": {"brand": "威風", "brand_wikidata": None, "category": Categories.RESTAURANT, "cuisine": "ramen"},
        "天下一": {"brand": "天下一", "brand_wikidata": None, "category": Categories.RESTAURANT, "cuisine": "ramen"},
        "久兵衛屋": {"brand": "久兵衛屋", "brand_wikidata": None, "category": Categories.RESTAURANT, "cuisine": "udon"},
    }

    async def start(self) -> AsyncIterator[FormRequest]:
        for index, prefecture in enumerate(PREFECTURES):
            # The search API is session-based: an initial search establishes
            # server-side result state (keyed by a cookie), and "morelist"
            # then pages through it, ignoring any "address" sent alongside.
            # Each prefecture therefore needs its own cookie jar so the 47
            # concurrent searches don't clobber each other's session state.
            yield FormRequest(
                "https://maps.zensho.co.jp/api/search",
                formdata={"address": prefecture},
                meta={"cookiejar": index},
                callback=self.parse_prefecture,
                cb_kwargs={"cookiejar": index},
            )

    def parse_prefecture(self, response: Response, cookiejar: int) -> Iterable[FormRequest]:
        # A large morelist value returns the full cumulative result set (no
        # prefecture has come close to 1000 stores) in a single follow-up
        # request against the session opened above.
        # Every prefecture's follow-up request has an identical URL and body
        # ("morelist=9999") - only the cookiejar (session) differs - so the
        # default dupefilter would otherwise treat all 47 as one request.
        yield FormRequest(
            "https://maps.zensho.co.jp/api/search",
            formdata={"morelist": "9999"},
            meta={"cookiejar": cookiejar},
            callback=self.parse_results,
            dont_filter=True,
        )

    def parse_results(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        data = response.json()

        addresses_by_ref = {}
        for li in scrapy.Selector(text=data["list"]).css("div.lists ul li"):
            href = li.css("a::attr(href)").get("")
            if ref_match := re.search(r"/detail/(\d+)\.html", href):
                addresses_by_ref[ref_match.group(1)] = {
                    "address": li.css("dl.address dd::text").get("").strip(),
                    "phone": li.css("dl.tel dd::text").get("").strip(),
                }

        for store in data.get("mapdata", []):
            ref_match = re.search(r"/detail/(\d+)\.html", store.get("link", ""))
            if not ref_match:
                continue
            ref = ref_match.group(1)

            brand_info = self.BRANDS.get(store.get("brand"))
            if not brand_info:
                self.logger.warning("Unmapped brand %r for ref %s, skipping", store.get("brand"), ref)
                continue

            item = Feature()
            item["ref"] = ref
            item["lat"] = store.get("lat")
            item["lon"] = store.get("lng")
            item["branch"] = store.get("name")
            item["website"] = f"https://maps.zensho.co.jp/jp/detail/{ref}.html"
            item["country"] = "JP"

            item["brand"] = brand_info["brand"]
            item["name"] = brand_info["brand"]
            if brand_info["brand_wikidata"]:
                item["brand_wikidata"] = brand_info["brand_wikidata"]
            apply_category(brand_info["category"], item)
            item["extras"]["cuisine"] = brand_info["cuisine"]

            extra = addresses_by_ref.get(ref, {})
            item["addr_full"] = extra.get("address") or None
            phone = extra.get("phone") or None
            # A shared national call-centre number, not branch-specific:
            # used verbatim by every なか卯/ゼッテリア/久兵衛屋 location.
            if phone != "0120-29-5770":
                item["phone"] = phone

            if oh := parse_hours(
                store.get("business_hour1", ""),
                store.get("business_hour2", ""),
                store.get("business_hour3", ""),
            ):
                item["opening_hours"] = oh.as_opening_hours()

            if "クレジットカード利用可" in store.get("options", []):
                apply_yes_no(PaymentMethods.CREDIT_CARDS, item, True)

            yield item
