import re
from typing import Any, Iterable
from urllib.parse import quote

import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, PaymentMethods, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

DAY_CHARS = {"月": "Mo", "火": "Tu", "水": "We", "木": "Th", "金": "Fr", "土": "Sa", "日": "Su"}
HOLIDAY_TOKENS_RE = re.compile("祝日|祭日|祝|、")
HOURS_RE = re.compile(r"([月火水木金土日祝、\-]*)\s*(\d{1,2}:\d{2})-(\d{1,2}:\d{2})")

# 48 search areas exposed by the store finder: Hokkaido is split into two
# halves ("01a"/"01b"), all other prefectures use their standard 2 digit code.
PREFECTURE_CODES = [
    "01a",
    "01b",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
    "10",
    "11",
    "12",
    "13",
    "14",
    "15",
    "16",
    "17",
    "18",
    "19",
    "20",
    "21",
    "22",
    "23",
    "24",
    "25",
    "26",
    "27",
    "28",
    "29",
    "30",
    "31",
    "32",
    "33",
    "34",
    "35",
    "36",
    "37",
    "38",
    "39",
    "40",
    "41",
    "42",
    "43",
    "44",
    "45",
    "46",
    "47",
]

ICON_MAP = {
    "手洗洗車": (Extras.CAR_WASH, True),
    "ドライブスルー洗車": (Extras.CAR_WASH, True),
    "車検": (Extras.VEHICLE_INSPECTION_SERVICES, True),
    "楽天車検取扱店": (Extras.VEHICLE_INSPECTION_SERVICES, True),
    "タイヤ": (Extras.VEHICLE_TYRE_SERVICES, True),
    "バッテリー": (Extras.VEHICLE_BATTERY_SERVICES, True),
    "オイル": (Extras.VEHICLE_OIL_CHANGE_SERVICES, True),
    "リペア": (Extras.VEHICLE_CAR_REPAIR_SERVICES, True),
    "EV充電サービス": (Fuel.ELECTRIC, True),
    "QUICPay取扱": (PaymentMethods.QUICPAY, True),
    "iD取扱": (PaymentMethods.ID, True),
    "nanaco": (PaymentMethods.NANACO, True),
    "楽天Edy": (PaymentMethods.EDY, True),
    "Apple Pay": (PaymentMethods.APPLE_PAY, True),
}


def expand_days(raw_day_part: str) -> list[str] | None:
    """Turn a Japanese day-of-week specifier (e.g. "月～土", "日祝", "平日")
    into a list of DAYS codes, or None if it can't be represented (e.g. a
    holiday-only ("祝") specifier, since this repo's OpeningHours has no
    concept of a separate "PH" day)."""
    if raw_day_part == "":
        return list(DAYS)

    stripped = HOLIDAY_TOKENS_RE.sub("", raw_day_part).strip()

    if "平日" in stripped:
        return ["Mo", "Tu", "We", "Th", "Fr"]

    if not stripped:
        return None

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


def parse_hours(hours_text: str) -> OpeningHours | None:
    hours_text = hours_text.strip()
    if not hours_text:
        return None
    if "24時間" in hours_text:
        oh = OpeningHours()
        for day in DAYS:
            oh.add_range(day, "00:00", "23:59")
        return oh

    text = hours_text.replace("〜", "-").replace("～", "-").replace("~", "-")
    text = re.sub(r"(\d{1,2})時(\d{1,2})分", r"\1:\2", text)
    text = re.sub(r"(\d{1,2})時", r"\1:00", text)

    oh = OpeningHours()
    found = False
    for day_part, open_time, close_time in HOURS_RE.findall(text):
        days = expand_days(day_part)
        if days is None:
            continue
        for day in days:
            oh.add_range(day, open_time, close_time)
        found = True

    return oh if found else None


class EneosJPSpider(scrapy.Spider):
    name = "eneos_jp"
    item_attributes = {"brand": "ENEOS", "brand_wikidata": "Q1640290"}
    allowed_domains = ["eneos-ss.com"]
    start_urls = ["https://eneos-ss.com/search/ss/pc/top.php"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[scrapy.Request]:
        for f_code in PREFECTURE_CODES:
            yield scrapy.FormRequest(
                "https://eneos-ss.com/search/ss/pc/kenmap.php",
                formdata={"f_code": f_code},
                callback=self.parse_kenmap,
                cb_kwargs={"f_code": f_code},
            )

    def parse_kenmap(self, response: Response, f_code: str) -> Iterable[scrapy.Request]:
        # Querying at the prefecture level truncates results once matches
        # exceed a server-side cap (confirmed: Toyama prefecture has 160
        # stations but a blank-municipality query silently returns only the
        # first 100). Each municipality (and, for the large cities that are
        # subdivided, each ward) is listed separately here and queried
        # individually below to stay under that cap.
        # A MAP query parameter (even empty) must be present or the server
        # redirects the request to error.php.
        municipalities = set(response.css(".searchWordNom li a::text").getall())
        for municipality in municipalities:
            url = "https://eneos-ss.com/search/ss/pc/listken.php" f"?f_code={f_code}&f_addr2={quote(municipality)}&MAP="
            yield scrapy.Request(url, callback=self.parse_listken)

    def parse_listken(self, response: Response, **kwargs: Any) -> Iterable[scrapy.Request]:
        if "設定最大値を超えました" in response.text:
            self.logger.warning(f"Result cap exceeded, results truncated: {response.url}")

        for dt in response.css("dl.ssList dt.n1eneos"):
            dd = dt.xpath("following-sibling::dd[1]")

            href = dt.css("a::attr(href)").get("")
            ref_match = re.search(r"SCODE=(\d+)", href)
            if not ref_match:
                continue
            ref = ref_match.group(1)

            name = dt.css("p.ssName::text").get("").strip()
            company = dt.css("p.ssName span::text").get("")
            tel = dt.css("p.ssTel::text").get("")
            hours_text = dt.xpath("./a/p[not(@class)]/text()").get("")

            address = dd.xpath("./a/p[1]/text()").get("")
            icon_alts = dd.css("ul.ssListIcon img::attr(alt)").getall()

            yield scrapy.Request(
                f"https://eneos-ss.com/search/ss/pc/detail.php?SCODE={ref}",
                callback=self.parse_detail,
                cb_kwargs={
                    "ref": ref,
                    "name": name,
                    "company": company,
                    "tel": tel,
                    "hours_text": hours_text,
                    "address": address,
                    "icon_alts": icon_alts,
                },
            )

    def parse_detail(self, response: Response, ref, name, company, tel, hours_text, address, icon_alts) -> Any:
        item = Feature()
        item["ref"] = ref
        item["name"] = "ENEOS"
        item["branch"] = name
        item["street_address"] = address.strip()
        item["country"] = "JP"
        item["phone"] = tel.strip() or None
        item["website"] = response.url

        # The detail page's own address block additionally includes the
        # postcode (which the municipality listing does not), e.g.
        # "930-0029　富山県富山市本町６－１７".
        addr_match = re.search(r"<dt>住所</dt>\s*<dd>(\d{3}-\d{4})[\s　]*(.*?)</dd>", response.text, re.S)
        if addr_match:
            item["postcode"] = addr_match.group(1)
            item["street_address"] = addr_match.group(2).strip()

        lon_match = re.search(r"cnsCenterLon\s*=\s*'([\d.\-]+)'", response.text)
        lat_match = re.search(r"cnsCenterLat\s*=\s*'([\d.\-]+)'", response.text)
        if lon_match and lat_match:
            item["lon"] = lon_match.group(1)
            item["lat"] = lat_match.group(1)

        if company:
            item["operator"] = company.strip()

        apply_category(Categories.FUEL_STATION, item)

        for alt in icon_alts:
            if alt == "フルサービス":
                item["extras"]["full_service"] = "yes"
            elif alt == "セルフ給油":
                item["extras"]["self_service"] = "yes"
            elif alt == "セブンイレブン併設":
                item["extras"]["sells:food"] = "yes"
            elif mapping := ICON_MAP.get(alt):
                apply_yes_no(mapping[0], item, mapping[1])

        oh = parse_hours(hours_text)
        if oh:
            item["opening_hours"] = oh.as_opening_hours()

        yield item
