import re
import unicodedata
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# Day words used in the free-text schedules ("Lunes a Viernes", "Lunes - Miercoles - Viernes", "Sábado"...).
DAY_WORDS = {
    "lunes": 0,
    "lun": 0,
    "l": 0,
    "martes": 1,
    "mar": 1,
    "miercoles": 2,
    "mie": 2,
    "jueves": 3,
    "jue": 3,
    "viernes": 4,
    "vie": 4,
    "v": 4,
    "sabado": 5,
    "sabados": 5,
    "sab": 5,
    "sa": 5,
    "s": 5,
    "domingo": 6,
    "domingos": 6,
    "dom": 6,
    "d": 6,
}
DAY_RE = re.compile(r"\b(" + "|".join(sorted(DAY_WORDS, key=len, reverse=True)) + r")\b")
TIME_RE = re.compile(r"(\d{1,2})(?:\s*[:.;]\s*(\d{2}))?\s*(am|pm|m\b)?")
TIME = r"\d{1,2}(?:\s*[:.;]\s*\d{2})?\s*(?:am|pm|m\b)?"
LUNCH_RE = re.compile(rf"almuerzo\s*(?:entre|de)\s*({TIME})\s*(?:y|a)\s*({TIME})")


def clean(value: str | None) -> str | None:
    value = re.sub(r"\s+", " ", value or "").strip(" -")
    return value or None


class SerpostPESpider(Spider):
    name = "serpost_pe"
    item_attributes = {"operator": "Serpost", "operator_wikidata": "Q19521863"}
    allowed_domains = ["www.serpost.com.pe"]
    # The office map on serpost.com.pe ("Red de oficinas") loads every point from this endpoint.
    start_urls = ["https://www.serpost.com.pe/Cliente/RedOficina/GetOficinas"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        offices = response.json()["oficinas"]
        # A few places carry a copy of another place's coordinates (two Cusco agents share a point 50 km out of
        # town); a point shared by different addresses is not trusted.
        addresses_at = {}
        for office in offices:
            addresses_at.setdefault((office["PLATITUD"], office["PLONGITUD"]), set()).add(office["PTODIRE"])
        for office in offices:
            kind = office["PTOTOFI"]
            if office["PTOVIGENTE"] != "1":
                continue
            if kind == "ALMACEN" or "PRUEBA" in (office["PTODIRE"] or ""):
                continue  # a warehouse, and a test record ("DIRECCIÓN PRUEBA")

            item = Feature()
            item["ref"] = str(office["IDOFICINA"])
            try:
                lat, lon = float(office["PLATITUD"]), float(office["PLONGITUD"])
                unique = len(addresses_at[(office["PLATITUD"], office["PLONGITUD"])]) == 1
                if unique and -18.5 < lat < 0 and -81.5 < lon < -68.5:
                    item["lat"], item["lon"] = lat, lon
            except (TypeError, ValueError):
                pass
            address = clean(office["PTODIRE"])
            if address and not address.upper().startswith("CONTAC"):  # "CONTACTARSE CON <phone> <staff name>"
                item["addr_full"] = address
            item["city"] = (clean(office["PTODIST"]) or "").title() or None
            item["state"] = (clean(office["PTODPTO"]) or "").title() or None
            item["opening_hours"] = self.parse_hours(office["PTODIAHORA"] or "")
            branch = clean(office["PTOLOCA"])

            if kind in ("OFICINA", "ADMINISTRACIÓN"):
                # "ADMINISTRACIÓN" is the head post office of a city or district (Cusco's at Av. El Sol 800,
                # Arequipa's at Calle Moral 118...), open to the public like any "OFICINA".
                item["branch"] = branch
                item["phone"] = "; ".join(
                    p for p in (clean(office["PTOTELFIJO"]), clean(office["PTOTELCEL"])) if p and re.search(r"\d{6}", p)
                )
                email = clean(office["PCORREOELECTRONICO"])
                if email and email.lower().endswith("@serpost.com.pe"):
                    item["email"] = email
                apply_category(Categories.POST_OFFICE, item)
            elif kind == "REPRESENTANTE":
                # Third-party agents: copy shops (T-Copia), travel agencies, rural "Tambo" service centres.
                # Their contact details are personal, so only the place is kept.
                if branch and "(T-Copia)" in branch:
                    item["name"] = "T-Copia"
                    branch = clean(branch.replace("(T-Copia)", ""))
                item["branch"] = branch
                apply_category(Categories.GENERIC_POI, item)
                item["extras"]["post_office"] = "post_partner"
            else:
                self.logger.warning("Unknown office type %s", kind)
                continue
            yield item

    @staticmethod
    def parse_hours(text: str) -> OpeningHours | None:
        """Parse free text such as "Lunes a Viernes de 9:00 a.m. a 5:00 p.m. / Sábado de 9:00 a.m. a 2:00 p.m."."""
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
            ranges = SerpostPESpider.parse_ranges(text[group[-1].end() : end])
            if ranges is None:
                return None
            rules.append((days, ranges))

        # Times written before the first day expression: "8 AM - 12 PM / 2 PM - 5 PM LUNES A SABADO" names the days
        # afterwards, and "8 AM - 12 PM / 2 PM - 6 PM SABADOS 8 AM - 12 PM" leaves the weekdays implied.
        leading = SerpostPESpider.parse_ranges(text[: groups[0][0].start()])
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
            times.append(SerpostPESpider.to_minutes(m, times[-1] if times else None))
            if times[-1] is None:
                return None
        if len(times) % 2:
            return None
        ranges = list(zip(times[::2], times[1::2]))
        if lunch:
            if len(ranges) != 1:
                return None
            lunch_start = SerpostPESpider.to_minutes(TIME_RE.match(lunch[0]), ranges[0][0])
            lunch_end = SerpostPESpider.to_minutes(TIME_RE.match(lunch[1]), lunch_start)
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
