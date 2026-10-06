import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

DAYS_RU = {"пн": "Mo", "вт": "Tu", "ср": "We", "чт": "Th", "пт": "Fr", "сб": "Sa", "вс": "Su"}
DAYS_RU_KEYS = list(DAYS_RU)
DAY_RE = "|".join(DAYS_RU_KEYS)
TOKEN_RE = re.compile(
    rf"(?P<day>{DAY_RE})|(?P<time>\d{{1,2}}[:.]\d{{2}})\s*-\s*(?P<end>\d{{1,2}}[:.]\d{{2}})|(?P<lunch>обед|перерыв)"
    r"|(?P<closed>выходн|демалыс)"  # day off (Russian, Kazakh)
)
# Post office types ("type_po") mapped as post offices: city (ГОПС), rural (СОПС), settlement (ПОПС) and other (ОПС)
# post offices, main post offices (Почтамт) and district service centres (ЦОУ).
POST_OFFICE_TYPES = {"ГОПС", "СОПС", "ПОПС", "ОПС", "Почтамт", "ЦОУ"}
FRANCHISE_TYPE = "Франчайзинг"  # franchised offices ("ФГО"/"ФСО") run by a local business


def clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return None if value in ("", "null") else value


class KazpostKZSpider(Spider):
    name = "kazpost_kz"
    allowed_domains = ["gateway.prod.qazpost.kz"]
    # The map at https://qazpost.kz/ru/map queries points by bounding box; this one covers all of Kazakhstan.
    start_urls = [
        "https://gateway.prod.qazpost.kz/mail-app/api/public/find_dep_fp"
        "?latitudeFrom=40&latitudeTo=56&longitudeFrom=46&longitudeTo=88"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for department in response.json():
            # Other types: ATMs, payment terminals, parcel lockers and "parcel supermarkets", EMS/courier and cargo
            # units, marketplace pick-up points, e-government kiosks, sorting and delivery units.
            if department["type_code"] != "dep" or department["status"] != "1":  # status 0: closed
                continue
            if department["type_po"] not in POST_OFFICE_TYPES and department["type_po"] != FRANCHISE_TYPE:
                continue
            item = Feature()
            item["ref"] = str(department["fp_id"])
            item["branch"] = clean(department["name"])
            item["lat"], item["lon"] = department["latitude"], department["longitude"]
            item["addr_full"] = re.sub(r"\s+", " ", department["address"] or "").strip() or None
            item["city"] = clean(department["naspunkt"])
            item["state"] = clean(department["oblast"])
            # "new_index" is the address's 2023 postcode (e.g. "C16D4B7"); "index" is the office's old 6-digit index.
            item["postcode"] = clean(department["new_index"])
            item["phone"] = clean(department["phone"])
            item["opening_hours"] = self.parse_hours(department["schedule"] or "")
            if department["type_po"] == FRANCHISE_TYPE:
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
                # e.g. 'ФГО ИП "Алинур"', "ФСО ИП Кәусар", 'ФГО ТОО «Best Price»-2'
                operator = re.sub(r"^Ф[ГСП]О\s+", "", item["branch"] or "")
                item["operator"] = re.sub(r"\s*\(.*\)$|-\d+$", "", operator).strip() or None
            else:
                # Set per item rather than in item_attributes: franchised offices are run by their franchisee.
                item["operator"], item["operator_wikidata"] = "Қазпошта", "Q746263"
                apply_category(Categories.POST_OFFICE, item)
            yield item

    def parse_hours(self, schedule: str) -> OpeningHours | None:
        # e.g. "пн-пт 09:00-18:00 обед 13:00-14:00 сб 09:00-14:00 вс - выходной",
        # "пн ср-пт 09:00-18:00 вт сб вс - выходной"; a lunch break applies to the group just before it.
        text = re.sub(r"без\s+(обеда?|перерыва)", " ", schedule.lower().replace("c", "с"))  # Latin "c" typos
        text = re.sub(
            rf"({DAY_RE})\s*-\s*({DAY_RE})",
            lambda m: " ".join(DAYS_RU_KEYS[DAYS_RU_KEYS.index(m[1]) : DAYS_RU_KEYS.index(m[2]) + 1]),
            text,
        )
        oh = OpeningHours()
        pending_days, group, lunch = [], None, False
        for token in TOKEN_RE.finditer(text):
            if token["day"]:
                pending_days.append(DAYS_RU[token["day"]])
            elif token["lunch"]:
                lunch = True
            elif token["time"]:
                start, end = (t.replace(".", ":").zfill(5) for t in (token["time"], token["end"]))
                if lunch:
                    if not group:
                        return None
                    days, (open_time, close_time) = group
                    group = (days, (open_time, start))
                    oh.add_days_range(days, end, close_time)
                    lunch = False
                else:
                    if group:
                        oh.add_days_range(group[0], *group[1])
                    if not pending_days:
                        return None
                    group, pending_days = (pending_days, (start, end)), []
            elif token["closed"]:
                if not pending_days:
                    return None
                oh.set_closed(pending_days)
                pending_days = []
        if group:
            oh.add_days_range(group[0], *group[1])
        if pending_days or lunch:
            return None
        return oh
