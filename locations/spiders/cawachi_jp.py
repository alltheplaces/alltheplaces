import calendar
import re
import unicodedata
from collections.abc import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, DAYS_JP, OpeningHours, sanitise_day
from locations.items import Feature
from locations.lang_utils import katakana_to_hiragana

# businessTypeName -> OSM category
CATEGORY = {
    "ドラッグ": Categories.SHOP_CHEMIST,
    "薬局": Categories.PHARMACY,
    "介護施設": Categories.SOCIAL_FACILITY,
}

# prefixStoreName -> brand_wikidata (only カワチ薬品 has a QID)
WIKIDATA = {"カワチ薬品": "Q11295397"}

# subStore businessTypeName -> ref suffix / website pharmacy flag
SUB_REF = {"薬局": "pharmacy", "介護施設": "care"}

STORE_URL = "https://www.cawachi.co.jp/customer/store/shop.html?storeCode={}"

TIME_RANGE = re.compile(r"(\d{1,2}:\d{2})~(\d{1,2}:\d{2})")

# weekday order used to expand a "月曜～金曜" range into single days
WEEK = ["月", "火", "水", "木", "金", "土", "日"]

# opening-hours month abbreviations for holiday date ranges
MONTHS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}

# a japanese date range used in regularHoliday, e.g. "12月29日～1月3日", "8月12日～17日", "1月1日"
JP_DATE = re.compile(
    r"(?P<start_month>\d{1,2})月(?P<start_day>\d{1,2})日"
    r"(?:[～~](?P<end_month>\d{1,2})月(?P<end_day>\d{1,2})日|[～~](?P<end_day_same>\d{1,2})日)?"
)


class CawachiJPSpider(Spider):
    """カワチ薬品 group stores, parsed from the JSON endpoint reachable from the store finder page."""

    name = "cawachi_jp"

    async def start(self) -> AsyncIterator[Request]:
        """Store data is in JSON file but filename (with YYYY + several digits) seems to be changed
        so we'll find the latest filename from ``store.js`` file"""
        yield Request(url="https://www.cawachi.co.jp/customer/store/", callback=self.parse_store_page)

    def parse_store_page(self, response: Response) -> Iterable[Request]:
        """Follow the site bundle that declares the store JSON endpoint."""
        if src := response.xpath("//script[contains(@src, 'store.js')]/@src").get():
            yield response.follow(src, callback=self.parse_store_js)

    def parse_store_js(self, response: Response) -> Iterable[Request]:
        """Resolve the store JSON path from the bundle's staging endpoint and fetch it."""
        if match := re.search(r"STAGING:\s*'([^']+)'", response.text):
            yield JsonRequest(url=response.urljoin(match.group(1)), callback=self.parse)

    def parse(self, response: Response) -> Iterable[Feature]:
        """Yield a POI per top-level store and per nested sub-store."""
        stores = response.json()["result"]["rows"]
        for store in stores:
            yield from self.parse_store(store)
            parent_code = store["storeCode"]
            for sub in store.get("subStores") or []:
                yield from self.parse_store(sub, parent_code)

    def parse_store(self, store: dict, parent_code: str | None = None) -> Iterable[Feature]:
        """Map one store record onto a Feature item."""
        item = Feature()
        item["lat"] = store["latitude"]
        item["lon"] = store["longitude"]
        item["state"] = store["prefecturesName"]
        item["city"] = store["city"]
        item["postcode"] = store["zipcode"]
        if building := store.get("buildingName"):
            item["street_address"] = unicodedata.normalize("NFKC", building)

        prefix = store["prefixStoreName"]
        item["brand"] = prefix
        if qid := WIKIDATA.get(prefix):
            item["brand_wikidata"] = qid

        business_type = store["businessTypeName"]
        if category := CATEGORY.get(business_type):
            apply_category(category, item)

        item["branch"] = store["storeName"]
        item["name"] = item["brand"]
        if kana := store.get("storeNameKana"):
            item["extras"]["branch:ja-Hira"] = katakana_to_hiragana(kana)
        item["phone"] = f"+81 {store['tel']}"
        if fax := store.get("fax"):
            item["extras"]["fax"] = f"+81 {fax}"
        apply_yes_no(Extras.PARKING, item, store.get("isParking", False), apply_positive_only=False)

        if hours := self.parse_hours(store.get("salesTime"), store.get("regularHoliday")):
            item["opening_hours"] = hours

        if parent_code is not None:
            item["ref"] = f"{parent_code}-{SUB_REF.get(business_type, 'sub')}"
            if business_type == "薬局":
                item["website"] = STORE_URL.format(parent_code) + "&pharmacy=1"
            else:
                item["website"] = STORE_URL.format(parent_code)
        else:
            item["ref"] = store["storeCode"]
            item["website"] = STORE_URL.format(store["storeCode"])

        yield item

    @staticmethod
    def parse_hours(sales_time: str | None, regular_holiday: str | None) -> str | None:
        """Build the opening-hours string from the store's hours and holiday fields."""
        if not sales_time:
            return None
        text = unicodedata.normalize("NFKC", sales_time).split("※")[0].strip()

        oh = OpeningHours()
        if any(day in text for day in DAYS_JP):
            CawachiJPSpider._parse_day_specific(oh, text)
        else:
            for open_time, close_time in TIME_RANGE.findall(text):
                for day in DAYS:
                    oh.add_range(day, open_time, close_time)

        result = oh.as_opening_hours()

        if regular_holiday and regular_holiday != "無":
            holiday = unicodedata.normalize("NFKC", regular_holiday)
            if "土曜" in holiday:
                oh.set_closed("Sa")
            if "日曜" in holiday:
                oh.set_closed("Su")
            result = oh.as_opening_hours()
            for off in CawachiJPSpider._holiday_offs(holiday):
                result = f"{result}; {off}" if result else off

        return result or None

    @staticmethod
    def _parse_day_specific(oh: OpeningHours, text: str) -> None:
        """Apply per-line day-specific hours, e.g. "月曜～金曜 9:00～18:00"."""
        for line in re.split(r"[\r\n]+", text):
            day_spec, _, times = line.partition(" ")
            if ":" not in times:
                continue
            for day in CawachiJPSpider._days_from_spec(day_spec):
                for open_time, close_time in TIME_RANGE.findall(times):
                    oh.add_range(day, open_time, close_time)

    @staticmethod
    def _days_from_spec(day_spec: str) -> list[str]:
        """Expand a japanese day spec into opening-hours day codes.

        Accepts a range ("月曜～金曜"), a list ("水曜・土曜") or a single day ("土曜").
        """
        if "～" in day_spec or "~" in day_spec:
            start_day, end_day = re.split(r"[～~]", day_spec, maxsplit=1)
            return CawachiJPSpider._expand_days(start_day[0], end_day[0])
        return [sanitise_day(token[0], DAYS_JP) for token in re.split(r"[・]", day_spec) if token]

    @staticmethod
    def _expand_days(start_day: str, end_day: str) -> list[str]:
        """Expand a weekday range such as 月～金 into the ordered day codes."""
        start_index = WEEK.index(start_day)
        end_index = WEEK.index(end_day)
        if end_index < start_index:
            end_index += len(WEEK)
        return [sanitise_day(WEEK[index % len(WEEK)], DAYS_JP) for index in range(start_index, end_index + 1)]

    @staticmethod
    def _holiday_offs(holiday: str) -> list[str]:
        """Turn japanese closure date ranges into opening-hours "off" clauses."""
        offs = []
        for match in JP_DATE.finditer(holiday):
            start_month = int(match["start_month"])
            start_day = int(match["start_day"])

            if match["end_month"]:  # e.g. 12月29日～1月3日
                end_month = int(match["end_month"])
                end_day = int(match["end_day"])
            elif match["end_day_same"]:  # e.g. 8月12日～17日
                end_month = start_month
                end_day = int(match["end_day_same"])
            else:  # single date, e.g. 1月1日
                offs.append(f"{MONTHS[start_month]} {start_day} off")
                continue

            if start_month == end_month:
                offs.append(f"{MONTHS[start_month]} {start_day}-{end_day} off")
            else:
                offs.append(f"{MONTHS[start_month]} {start_day}-{MONTHS[end_month]} {end_day} off")
        return offs
