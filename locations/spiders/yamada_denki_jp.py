import json
import re
from collections.abc import AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_JP, DAYS_WEEKDAY, DAYS_WEEKEND, OpeningHours
from locations.items import Feature

BASE_URL = "https://www.yamada-denki.jp/store/contents/"

# `?p=1..47` pages correspond to these prefectures.
PREFECTURES = [
    "北海道",
    "青森県",
    "岩手県",
    "宮城県",
    "秋田県",
    "山形県",
    "福島県",
    "茨城県",
    "栃木県",
    "群馬県",
    "埼玉県",
    "千葉県",
    "東京都",
    "神奈川県",
    "新潟県",
    "富山県",
    "石川県",
    "福井県",
    "山梨県",
    "長野県",
    "岐阜県",
    "静岡県",
    "愛知県",
    "三重県",
    "滋賀県",
    "京都府",
    "大阪府",
    "兵庫県",
    "奈良県",
    "和歌山県",
    "鳥取県",
    "島根県",
    "岡山県",
    "広島県",
    "山口県",
    "徳島県",
    "香川県",
    "愛媛県",
    "高知県",
    "福岡県",
    "佐賀県",
    "長崎県",
    "熊本県",
    "大分県",
    "宮崎県",
    "鹿児島県",
    "沖縄県",
]

# brand -> (brand_wikidata, category)
BRANDS = {
    "ヤマダデンキ": ("Q1096390", Categories.SHOP_ELECTRONICS),
    "ベスト電器": ("Q701925", Categories.SHOP_ELECTRONICS),
    "マツヤデンキ": ("Q11340620", Categories.SHOP_ELECTRONICS),
    "コスモスベリーズ": ("Q11302120", Categories.SHOP_ELECTRONICS),
    "大塚家具": ("Q11434017", Categories.SHOP_FURNITURE),
    "ツクモ": ("Q29793996", Categories.SHOP_COMPUTER),
    "キムラヤ": (None, Categories.SHOP_CHEMIST),
    "ポルトローナ・フラウ": ("Q1477785", Categories.SHOP_FURNITURE),
    "ロルフベンツ": ("Q2163232", Categories.SHOP_FURNITURE),
}
DEFAULT_BRAND = "ヤマダデンキ"

NAME_PREFIXES = [
    ("ベスト電器", "ベスト電器"),
    ("マツヤデンキ", "マツヤデンキ"),
    ("コスモスベリーズ", "コスモスベリーズ"),
    ("DEPOツクモ", "ツクモ"),
    ("TSUKUMO", "ツクモ"),
    ("ツクモ", "ツクモ"),
    ("キムラヤ", "キムラヤ"),
    ("家電住まいる館×YAMADA web.com", "ヤマダデンキ"),
    ("家電住まいる館YAMADA", "ヤマダデンキ"),
    ("YAMADA New web.com", "ヤマダデンキ"),
    ("YAMADA TAX FREE", "ヤマダデンキ"),
    ("YAMADA web.com", "ヤマダデンキ"),
    ("Tecc LIFE SELECT", "ヤマダデンキ"),
    ("IDC OTSUKA OUTLET&BedroomGallery", "大塚家具"),
    ("IDC OTSUKA", "大塚家具"),
    ("大塚家具", "大塚家具"),
    ("ヤマダアウトレット", "ヤマダデンキ"),
    ("ヤマダファミリーショップ", "ヤマダデンキ"),
    ("テックランド", "ヤマダデンキ"),
    ("LABI LIFE SELECT", "ヤマダデンキ"),
    ("LABI1 LIFE SELECT", "ヤマダデンキ"),
    ("LABI", "ヤマダデンキ"),
    ("ポルトローナ・フラウ", "ポルトローナ・フラウ"),
    ("ロルフベンツ", "ロルフベンツ"),
]

TIME_SEGMENT_RE = re.compile(r"([^\d]*?)(\d{1,2}:\d{2})[～~](\d{1,2}:\d{2})(?:[（(]([^)）]*)[)）])?")


class YamadaDenkiJPSpider(Spider):
    name = "yamada_denki_jp"

    async def start(self) -> AsyncIterator[Request]:
        """Fetch one listing page per prefecture to collect store detail ids."""
        for page, pref in enumerate(PREFECTURES, start=1):
            yield Request(url=f"{BASE_URL}?p={page}", callback=self.parse_list, meta={"state": pref})

    def parse_list(self, response: Response) -> Iterable[Request]:
        """Follow each store's detail page, passing the prefecture for state."""
        for box in response.xpath('//div[contains(concat(" ", normalize-space(@class), " "), " shop-box ")]'):
            href = box.xpath('.//h3[contains(@class,"shop-name")]/a/@href').get()
            if not (match := re.search(r"\?d=(\d+)", href)):
                continue
            yield Request(
                url=f"{BASE_URL}?d={match.group(1)}",
                callback=self.parse_store,
                meta={"state": response.meta["state"]},
            )

    def parse_store(self, response: Response) -> Iterable[Feature]:
        name = response.xpath("//h1/text()").get().strip()
        brand, brand_qid, branch = self._classify_name(name)

        item = Feature()
        item["ref"] = re.search(r"\?d=(\d+)", response.url).group(1)
        item["name"] = brand
        item["branch"] = branch
        item["brand"] = brand
        if brand_qid:
            item["brand_wikidata"] = brand_qid
        item["website"] = response.url
        item["state"] = response.meta["state"]

        if addr := response.xpath("//div[starts-with(normalize-space(.), '〒')]/text()").get():
            addr = addr.strip()
            if postcode := re.search(r"(\d{3}-\d{4})", addr):
                item["postcode"] = postcode.group(1)
                addr = addr.replace("〒", "").replace(postcode.group(1), "").strip()
            item["addr_full"] = addr

        if hours := response.xpath('//div[starts-with(normalize-space(.), "営業時間")]/text()').get():
            item["opening_hours"] = self._parse_hours(hours)

        if tel := response.xpath('string(//div[contains(@class,"shopdetail3l")])').get():
            if m := re.search(r"\d[\d-]*", tel):
                item["phone"] = f"+81 {m.group()}"
        if fax := response.xpath('string(//div[contains(@class,"shopdetail3r")])').get():
            if m := re.search(r"\d[\d-]*", fax):
                item["extras"]["fax"] = f"+81 {m.group()}"

        if lat_lon := self._get_coordinates(response):
            item["lat"], item["lon"] = lat_lon

        apply_category(BRANDS[brand][1], item)
        yield item

    def _classify_name(self, name: str) -> tuple[str, str | None, str]:
        """Return (brand, wikidata, branch) from a store name."""
        for prefix, brand in NAME_PREFIXES:
            if name.startswith(prefix):
                return brand, BRANDS[brand][0], name[len(prefix) :].strip()
        return DEFAULT_BRAND, BRANDS[DEFAULT_BRAND][0], name

    def _get_coordinates(self, response: Response) -> tuple[float, float] | None:
        """Match the store in the prefecture-wide ``map_shops`` coordinate array."""
        script = response.xpath('//script[contains(text(), "var map_shops")]/text()').get()
        if not script:
            return None
        try:
            shops = json.loads(script.split("var map_shops =", 1)[1].split("];", 1)[0] + "]")
        except json.JSONDecodeError:
            return None
        for shop in shops:
            if f"?d={self._store_id(response.url)}" in shop.get("html", ""):
                try:
                    return float(shop["lat"]), float(shop["lon"])
                except (KeyError, TypeError, ValueError):
                    return None
        return None

    @staticmethod
    def _store_id(url: str) -> str:
        return re.search(r"\?d=(\d+)", url).group(1)

    def _parse_hours(self, raw: str) -> str | None:
        text = raw.replace("営業時間", "").strip(" :：").split("※")[0].strip()
        if not text:
            return None

        if "24時間" in text:
            return "24/7"

        closing = ""
        if "定休日" in text:
            text, closing = text.split("定休日", 1)
            closing = "定休日" + closing
        oh, holiday_ranges = self._build_time_ranges(text)
        if not oh:
            return None

        result = oh.as_opening_hours()
        if holiday_ranges:
            result = f"{result}; " + "; ".join(f"PH {o}-{c}" for o, c in holiday_ranges)
        # hours.py doesn't support the ordinal off like every nth Monday so manually append string
        if offs := self._closing_offs(closing):
            result = f"{result}; {'; '.join(offs)}"
        return result

    @staticmethod
    def _build_time_ranges(text: str) -> tuple[OpeningHours | None, list[tuple[str, str]]]:
        """Split the hours text into day-scoped time ranges and build the OpeningHours.

        Returns (OpeningHours, holiday ranges) where holiday ranges are the
        opening times of any 祝日 (public holiday) group, to be appended as PH.
        """
        time_segments = TIME_SEGMENT_RE.findall(text)
        if not time_segments:
            return None, []

        base = None
        scoped: list[tuple[set[str], str, str]] = []
        covered: set[str] = set()
        holiday_ranges: list[tuple[str, str]] = []
        for dayspec, open_t, close_t, trail in time_segments:
            dayspec = f"{dayspec} {trail}".strip()
            if "祝" in dayspec:
                holiday_ranges.append((open_t, close_t))
            codes = YamadaDenkiJPSpider._day_codes(dayspec)
            if codes is None:
                base = (open_t, close_t)
            else:
                scoped.append((codes, open_t, close_t))
                covered |= codes

        oh = OpeningHours()
        if not scoped and base:
            oh.add_days_range(DAYS, *base)
        elif scoped:
            if base:
                oh.add_days_range([d for d in DAYS if d not in covered], *base)
            for codes, open_t, close_t in scoped:
                oh.add_days_range(sorted(codes), open_t, close_t)
        return oh, holiday_ranges

    @staticmethod
    def _day_codes(dayspec: str) -> set[str] | None:
        """Expand a japanese day spec into day codes. None means 'all days' (base)."""
        dayspec = dayspec.strip("、/，, \u3000()（）")
        if not dayspec:
            return None
        codes: set[str] = set()
        for token in re.split(r"[・、，/ ]+", dayspec.replace("祝", " 祝")):
            token = token.strip()
            if not token:
                # 祝 (public holiday) is handled separately as PH at the segment
                continue
            if token == "平日":
                codes |= set(DAYS_WEEKDAY)
            elif token == "土日":
                codes |= set(DAYS_WEEKEND)
            elif "～" in token or "~" in token:
                start, end = re.split(r"[～~]", token)
                if start.endswith("曜"):
                    start += "日"
                if end.endswith("曜"):
                    end += "日"
                start_index = DAYS.index(DAYS_JP[start])
                end_index = DAYS.index(DAYS_JP[end])
                codes |= set(
                    DAYS[start_index : end_index + 1]
                    if start_index <= end_index
                    else DAYS[start_index:] + DAYS[: end_index + 1]
                )
            else:
                if token.endswith("曜"):
                    token += "日"
                if token in DAYS_JP:
                    codes.add(DAYS_JP[token])
        return codes

    @staticmethod
    def _closing_offs(closing: str) -> list[str]:
        """Convert the 定休日 string (e.g. 第2水曜日・水曜日) into OSM 'off' clauses."""
        if not closing:
            return []
        closing = closing.replace("定休日", "").strip(":：・ ")

        nth_weekdays: dict[str, set[int]] = {}
        plain_weekdays: set[str] = set()
        for match in re.finditer(r"第(\d)([月火水木金土日])曜日|([月火水木金土日])曜日", closing):
            weekday = match.group(2)
            weekday_2 = match.group(3)
            if nth := match.group(1):
                nth_weekdays.setdefault(weekday, set()).add(int(nth))
            else:
                plain_weekdays.add(weekday_2)

        clauses: list[str] = []
        for weekday, nth_numbers in nth_weekdays.items():
            clauses.append(f"{DAYS_JP[weekday]}[{','.join(map(str, sorted(nth_numbers)))}] off")
        for weekday in plain_weekdays:
            if weekday not in nth_weekdays:
                clauses.append(f"{DAYS_JP[weekday]} off")
        if "祝日" in closing:
            clauses.append("PH off")
        return clauses
