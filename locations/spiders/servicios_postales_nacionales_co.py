import json
import re
import unicodedata
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_ES, OpeningHours
from locations.items import Feature

# Day words used in the free-text schedules ("L-V", "Lun-Mié", "Lunes a Viernes", "SAB", "S"...).
# They are the DAYS_ES names, lower-cased and accent-stripped like the text, mapped to the day's index in DAYS.
DAY_WORDS = {
    unicodedata.normalize("NFKD", word.lower()).encode("ascii", "ignore").decode(): DAYS.index(day)
    for word, day in DAYS_ES.items()
}
DAY_RE = re.compile(r"\b(" + "|".join(sorted(DAY_WORDS, key=len, reverse=True)) + r")\b")
TIME_RE = re.compile(r"(\d{1,2})(?:\s*[:.;]\s*(\d{2}))?\s*(am|pm|m\b)?")
TIME = r"\d{1,2}(?:\s*[:.;]\s*\d{2})?\s*(?:am|pm|m\b)?"
LUNCH_RE = re.compile(rf"almuerzo\s*(?:entre|de)\s*({TIME})\s*(?:y|a)\s*({TIME})")


class ServiciosPostalesNacionalesCOSpider(Spider):
    name = "servicios_postales_nacionales_co"
    item_attributes = {"operator": "4-72", "operator_wikidata": "Q85800448"}
    allowed_domains = ["www.4-72.com.co"]
    # The agency finder embeds every point in the page as `var initMarkers = [...]`.
    start_urls = ["https://www.4-72.com.co/buscador-de-agencias/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        start = response.text.index("var initMarkers = ") + len("var initMarkers = ")
        markers, _ = json.JSONDecoder().raw_decode(response.text[start:])
        for point in markers:
            kind = point["type"]
            if point.get("status") != "1":
                continue
            if kind == "Oficinas de atención al cliente":
                # Customer-service (claims) desks; each shares its building with a "Punto de venta" listed separately.
                continue
            schedule = " ".join(point.get("schedules") or []).strip()
            if schedule.lower().startswith("cerrado"):
                continue  # "Cerrado temporalmente", "cerrado fuerza Mayor"

            item = Feature()
            item["ref"] = point["id"]
            item["lat"], item["lon"] = point["lat"], point["lng"]
            item["street_address"] = point["address"]
            item["city"] = point["city"].strip()
            item["state"] = point["region"].strip()
            # Often several numbers, sometimes with the first name of who answers ("3145507451(JAIME)3145926423").
            item["phone"] = (
                "; ".join(m.strip() for m in re.findall(r"\(?\d[\d\s()]{5,}\d", point["phone"] or "")) or None
            )
            item["opening_hours"] = self.parse_hours(schedule)

            if kind == "Puntos de venta":
                # 4-72's own counters ("PV. ARMENIA").
                item["branch"] = re.sub(r"^PV\.\s*", "", point["name"]).strip()
                apply_category(Categories.POST_OFFICE, item)
            elif kind == "Expendio SPU":
                # Universal-postal-service outlets run by contracted third parties ("cada tercero contratado"),
                # usually a shop in a small municipality.
                item["branch"] = re.sub(r"^EXPENDIO SPU\s*", "", point["name"]).strip()
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            elif kind == "Aliado comercial":
                # Retail partners; names are those of the sole traders who run them, so they are not kept.
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            else:
                self.logger.warning("Unknown point type %s", kind)
                continue
            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours | None:
        """Parse free text such as "L-V 8-12 -14-18 - S 8-12" or "Lunes a viernes de 8 a 12 y de 2 a 6p.m."."""
        text = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
        text = re.sub(r"\b([ap])\s*\.?\s*m\b\.?", r"\1m", text)
        text = re.sub(r"\blv\b", "l-v", text)

        # Group adjacent day words ("lunes a viernes", "l - v", "martes y jueves") into day expressions.
        groups = []
        for match in DAY_RE.finditer(text):
            joiner = text[groups[-1][-1].end() : match.start()] if groups else None
            if joiner is not None and re.fullmatch(r"\s*(a|al|hasta|-|y|,|e)?\s*", joiner):
                groups[-1].append(match)
            else:
                groups.append([match])
        if not groups:
            return None

        rules = []  # (days, ranges)
        for i, group in enumerate(groups):
            days = [DAY_WORDS[group[0].group(1)]]
            for previous, match in zip(group, group[1:]):
                day = DAY_WORDS[match.group(1)]
                joiner = text[previous.end() : match.start()].strip()
                # "L-V", "Lunes a Viernes" and "LUN SAB" are ranges; "Martes y Jueves", "Lunes - Miercoles - Viernes"
                # are lists.
                if joiner in ("a", "al", "hasta") or (joiner in ("-", "") and len(group) == 2):
                    if day < days[-1]:
                        return None
                    days.extend(range(days[-1] + 1, day + 1))
                else:
                    days.append(day)
            end = groups[i + 1][0].start() if i + 1 < len(groups) else len(text)
            ranges = ServiciosPostalesNacionalesCOSpider.parse_ranges(text[group[-1].end() : end])
            if ranges is None:
                return None
            rules.append((days, ranges))

        # Times written before the first day expression: "8 AM - 12 PM / 2 PM - 5 PM LUNES A SABADO" names the days
        # afterwards, and "8 AM - 12 PM / 2 PM - 6 PM SABADOS 8 AM - 12 PM" leaves the weekdays implied.
        leading = ServiciosPostalesNacionalesCOSpider.parse_ranges(text[: groups[0][0].start()])
        if leading is None:
            return None
        if leading:
            if not rules[0][1]:
                rules[0] = (rules[0][0], leading)
            elif rules[0][0] == [5]:
                rules.insert(0, (list(range(5)), leading))
            else:
                return None

        oh = OpeningHours()
        for days, ranges in rules:
            for day in days:
                for start, close in ranges:
                    oh.add_range(DAYS[day], "%02d:%02d" % divmod(start, 60), "%02d:%02d" % divmod(close, 60))
        return oh

    @staticmethod
    def parse_ranges(segment: str) -> list[tuple[int, int]] | None:
        """Read the times in a segment as consecutive open/close pairs, in minutes. None if they do not make sense."""
        if "cerrado" in segment or "no se atiende" in segment:
            return []
        lunch = None
        if m := LUNCH_RE.search(segment):
            lunch = m.group(1), m.group(2)
            segment = segment[: m.start()] + segment[m.end() :]
        times = []
        for m in TIME_RE.finditer(segment):
            times.append(ServiciosPostalesNacionalesCOSpider.to_minutes(m, times[-1] if times else None))
            if times[-1] is None:
                return None
        if len(times) % 2:
            return None
        ranges = list(zip(times[::2], times[1::2]))
        if lunch:
            if len(ranges) != 1:
                return None
            lunch_start = ServiciosPostalesNacionalesCOSpider.to_minutes(TIME_RE.match(lunch[0]), ranges[0][0])
            lunch_end = ServiciosPostalesNacionalesCOSpider.to_minutes(TIME_RE.match(lunch[1]), lunch_start)
            if lunch_start is None or lunch_end is None:
                return None
            ranges = [(ranges[0][0], lunch_start), (lunch_end, ranges[0][1])]
        previous_end = 0
        for start, close in ranges:
            if not previous_end <= start < close <= 24 * 60:
                return None
            previous_end = close
        return ranges

    @staticmethod
    def to_minutes(m: re.Match, previous: int | None) -> int | None:
        hour, minute, suffix = int(m.group(1)), int(m.group(2) or 0), m.group(3)
        if hour > 24 or minute > 59:
            return None
        if suffix == "pm" and hour < 12:
            hour += 12
        elif suffix != "am" and not (suffix == "m" and hour == 12):
            # A bare time (or "1:00 m") earlier than the one before it is in the afternoon: "de 8 a 12 y de 2 a 6".
            if previous is not None and hour * 60 + minute <= previous and hour < 12:
                hour += 12
        return hour * 60 + minute
