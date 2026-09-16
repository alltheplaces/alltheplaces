import json
import re
import unicodedata
from typing import AsyncIterator, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, PaymentMethods, apply_category, apply_yes_no
from locations.geo import bbox_split
from locations.hours import DAYS, DAYS_WEEKDAY, OpeningHours, day_range
from locations.items import Feature

# 曜日 kanji used in 【月～土】-style open-time day prefixes.
JP_DAYS = {"月": "Mo", "火": "Tu", "水": "We", "木": "Th", "金": "Fr", "土": "Sa", "日": "Su"}

# Bounding box comfortably covering all of Japan, including Okinawa.
JAPAN_BBOX = ((46.0, 122.0), (20.0, 150.0))

# GET /search/getMapData.php returns a JSON array of lots for a lat/lng view rectangle.
# It silently truncates at 50 rows per request
RESULT_CAP = 50

# Stop subdividing below this span to guarantee termination even when
# many co-located lots (e.g. several facilities at one building) exceed the cap.
MIN_SPAN_DEGREES = 0.001


class NaviparkJPSpider(Spider):
    name = "navipark_jp"
    item_attributes = {"brand": "ナビパーク", "brand_wikidata": "Q116975255"}
    allowed_domains = ["www.navipark1.com"]

    async def start(self) -> AsyncIterator[Request]:
        for bbox in bbox_split(JAPAN_BBOX, lat_parts=4, lon_parts=4):
            yield self.make_request(bbox)

    def make_request(self, bbox: tuple[tuple[float, float], tuple[float, float]]) -> Request:
        (north_lat, west_lon), (south_lat, east_lon) = bbox
        url = (
            "https://www.navipark1.com/search/getMapData.php"
            f"?latFrom={south_lat}&latTo={north_lat}&lngFrom={west_lon}&lngTo={east_lon}"
        )
        return Request(url, callback=self.parse, cb_kwargs={"bbox": bbox})

    def parse(
        self, response: Response, bbox: tuple[tuple[float, float], tuple[float, float]]
    ) -> Iterable[Feature | Request]:
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return
        if not data:
            return

        # API silently truncates the result array to RESULT_CAP
        # so recursively subdivide the bbox area until no truncation observed.
        (north_lat, west_lon), (south_lat, east_lon) = bbox
        if (
            len(data) >= RESULT_CAP
            and (north_lat - south_lat) > MIN_SPAN_DEGREES
            and (east_lon - west_lon) > MIN_SPAN_DEGREES
        ):
            for sub_bbox in bbox_split(bbox, lat_parts=2, lon_parts=2):
                yield self.make_request(sub_bbox)
            return

        for lot in data:
            yield self.parse_lot(lot)

    def parse_lot(self, lot: dict) -> Feature:
        # The lot's unique code, present under two keys: propertyCD and KHNVCD.
        lot_code = lot.get("propertyCD") or lot.get("KHNVCD")

        item = Feature()
        item["ref"] = lot_code
        item["branch"] = unicodedata.normalize("NFKC", lot.get("propertyName") or lot.get("KHNVNM"))
        item["addr_full"] = unicodedata.normalize("NFKC", lot.get("propertyAddress"))
        item["operator"] = "スターツアメニティー"
        item["operator_wikidata"] = "Q116975260"

        # Some records (e.g. N06917) returns broken coordinate strings like trailing comma
        # in propertyIdo ('35.769406934909426,').
        item["lat"] = re.sub(r"[^\d.]", "", lot.get("propertyIdo") or "")
        item["lon"] = re.sub(r"[^\d.]", "", lot.get("propertyKeido") or "")

        item["website"] = f"https://www.navipark1.com/parkingDetail/{lot_code}.html"

        if zip1 := lot.get("propertyZipCode1"):
            if zip2 := lot.get("propertyZipCode2"):
                item["postcode"] = f"{zip1}-{zip2}"

        # 時間貸区画 (time-rental capacity); rendered on the detail and list
        # pages, e.g. N00025 KHDISU='3' shows "時間貸区画 3台".
        if capacity := lot.get("KHDISU"):
            item["extras"]["capacity"] = capacity

        if open_time := lot.get("openTime"):
            if hours := self.parse_open_hours(open_time):
                item["opening_hours"] = hours

        for key, value in self.parse_vehicle_limits(lot.get("vehicleLimit") or "").items():
            item["extras"][key] = value

        # Flag key was from the site's own icon legend (detail pages render ic06/ic15 for these):
        # - クレジット対応 -> payment by credit card
        # - アプリ決済対応 -> payment by app
        # Other feature flags (gate/lock type, max rate, voucher sales, points program, etc.) are skipped.
        apply_yes_no(PaymentMethods.CREDIT_CARDS, item, lot.get("feature6") == "1")
        apply_yes_no(PaymentMethods.APP, item, lot.get("feature15") == "1")

        apply_category(Categories.PARKING, item)

        return item

    @staticmethod
    def parse_open_hours(text: str) -> OpeningHours | None:
        if text == "24時間":
            oh = OpeningHours()
            for day in DAYS:
                oh.add_range(day, "00:00", "24:00")
            return oh

        # Strings that has no parseable hours, pointing instead to the remarks field.
        if text in ("備考欄に記載", "掲載用備考へ記載"):
            return None

        # Normalise full-width digits, colon, tilde and minus to ASCII, then
        # turn kanji 時 ("9時") into :00 notation.
        text = text.translate(str.maketrans("０１２３４５６７８９：～－−", "0123456789:---"))
        text = re.sub(r"(\d+)時", r"\1:00", text)

        days = DAYS
        if text.startswith("平日"):
            days = DAYS_WEEKDAY
            text = text[len("平日") :]
        if m := re.match(r"【(.+?)】", text):
            start_jp, sep, end_jp = m.group(1).partition("-")
            days = day_range(JP_DAYS[start_jp], JP_DAYS[end_jp]) if sep else [JP_DAYS[start_jp]]
            text = text[m.end() :]

        if not (m := re.match(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", text.strip())):
            return None

        oh = OpeningHours()
        for day in days:
            oh.add_range(day, f"{m.group(1)}:{m.group(2)}", f"{m.group(3)}:{m.group(4)}")
        return oh

    @staticmethod
    def parse_vehicle_limits(text: str) -> dict[str, str]:
        limits: dict[str, str] = {}
        patterns = {
            "maxheight": r"高さ([\d.]+)m",
            "maxlength": r"長さ([\d.]+)m",
            "maxwidth": r"幅([\d.]+)m",
            "maxweight": r"重量([\d.]+)t",
        }
        for key, pattern in patterns.items():
            if m := re.search(pattern, text):
                limits[key] = m.group(1)
        return limits
