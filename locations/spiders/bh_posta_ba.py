import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

# "08:00-16:00", "08-16", "07-15:30", "08:00 – 17:30"
TIME_RANGE_RE = re.compile(r"(?<![\d:])(\d{1,2})(?::(\d{2}))?\s*[-–]\s*(\d{1,2})(?::(\d{2}))?(?![\d:])")
# Day labels: "(pon.-pet.)" after a time range, or "(pon.-pet.):" / "subota:" / "(Subota)" before one.
PAREN_RE = re.compile(r"\(([^()]*)\)")
DATE_RE = re.compile(r"\b\d{1,2}\.\s?\d{1,2}\.(?:\s?\d{4}\.?)?")
CLOSED_RE = re.compile(r"zatvoren|neće raditi", re.IGNORECASE)
# Saturday opening that only applies on some Saturdays ("prve dvije subote", "zadnje dvije subote su
# neradne", "Subotom ne radi osim kad je isplata penzija", ...) can't be expressed simply, so Saturday
# is dropped when any such qualifier is present.
PARTIAL_SATURDAY_RE = re.compile(r"prv[aei]|zadnj|osim|penzij|ostale ne radi|druga subota", re.IGNORECASE)
# Hours that vary by week of the month, or that mix counter and delivery shifts, are not parsed.
UNPARSEABLE_RE = re.compile(r"sedmic|dostav|u objektu", re.IGNORECASE)


class BhPostaBaSpider(Spider):
    name = "bh_posta_ba"
    item_attributes = {"operator": "BH Pošta", "operator_wikidata": "Q4835619"}
    allowed_domains = ["www.posta.ba"]
    start_urls = ["https://www.posta.ba/postanska-mreza/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # The network map ("WP Google Map Gold" plugin) embeds every office as JSON: "places":[...].
        decoder = json.JSONDecoder()
        for match in re.finditer(r'"places":\[', response.text):
            places, _ = decoder.raw_decode(response.text, match.end() - 1)
            if not isinstance(places, list):
                continue
            for place in places:
                if not isinstance(place, dict) or place.get("id") is None or not place.get("title"):
                    continue
                if item := self.parse_place(place):
                    yield item

    def parse_place(self, place: dict) -> Feature | None:
        location = place.get("location") or {}
        fields = location.get("extra_fields") or {}
        hours_text = re.sub(r"<!--.*?-->", " ", fields.get("radno-vrijeme") or "", flags=re.DOTALL)
        if CLOSED_RE.search(hours_text) and not re.search(r"\bdo\b|\d\.\s*-\s*\d", hours_text, re.IGNORECASE):
            # "PRIVREMENO ZATVORENA", "ZATVORENO", "POŠTA ĆE BITI ZATVORENA OD 01.10.2023. GODINE": closed
            # with no end date. Closures with an end date ("... OD 13.07. DO 31.07.2026.") are kept.
            self.crawler.stats.inc_value("atp/bh_posta_ba/closed_skipped")
            return None

        title = re.sub(r"\s+", " ", place["title"]).strip()  # "71101 Sarajevo", "71162 Sarajevo - Sud BiH"
        item = Feature()
        item["ref"] = place["id"]
        # Strip stray separators: one office has "lat": "44.884851,".
        item["lat"], item["lon"] = (str(location.get(key) or "").strip(" ,") or None for key in ("lat", "lng"))
        if m := re.match(r"(\d{5})\s*(.*)", title):
            item["postcode"], item["branch"] = m.group(1), m.group(2)
        else:
            item["branch"] = title
        item["street_address"] = (fields.get("adresa") or "").strip() or None
        item["city"] = location.get("city") or None
        item["phone"] = (fields.get("telefon") or "").strip() or None
        if fax := (fields.get("fax") or "").strip():
            item["extras"]["fax"] = fax
        item["opening_hours"] = self.parse_hours(hours_text)
        apply_category(Categories.POST_OFFICE, item)
        return item

    def parse_hours(self, text: str) -> OpeningHours | None:
        oh = OpeningHours()
        text = re.sub(r"</?br\s*/?>", " ; ", text, flags=re.IGNORECASE)
        text = DATE_RE.sub(" ", text)
        if not text.strip() or UNPARSEABLE_RE.search(text):
            return None
        partial_saturday = bool(PARTIAL_SATURDAY_RE.search(text))
        ranges = list(TIME_RANGE_RE.finditer(text))
        parsed = False
        used_until = 0  # end of the label consumed by the previous range, so it isn't reused
        for i, rng in enumerate(ranges):
            following = text[rng.end() : ranges[i + 1].start() if i + 1 < len(ranges) else len(text)]
            preceding = text[max(ranges[i - 1].end() if i else 0, used_until) : rng.start()]
            # A label right after the range ("08:00-16:00 (pon.-pet.)", "08:00-13:00 sub.") wins; otherwise
            # the last label before it ("(pon.-pet.): 08:00-15:00", "subota: 08:00-13:00").
            if m := re.match(r"[\s,]*(?:\(([^()]*)\)?|(sub)(?:ota)?\b\.?(?!\s*:))", following, re.IGNORECASE):
                days = self.label_days(m.group(1) or m.group(2) or "")
                used_until = rng.end() + m.end()
            else:
                labels = PAREN_RE.findall(preceding) + re.findall(r"\b(subota)\s*:", preceding, re.IGNORECASE)
                days = self.label_days(labels[-1]) if labels else None
            if not days:
                continue
            if partial_saturday:
                days = [d for d in days if d != "Sa"]
            h1, m1, h2, m2 = rng.groups()
            if int(h1) > 24 or int(h2) > 24:
                continue
            oh.add_days_range(days, f"{h1}:{m1 or '00'}", f"{h2}:{m2 or '00'}")
            parsed = True
        if not parsed:
            self.crawler.stats.inc_value("atp/bh_posta_ba/hours_unparsed")
            return None
        return oh

    @staticmethod
    def label_days(label: str) -> list[str] | None:
        label = label.lower()
        if re.search(r"pon\W*pet", label):
            return DAYS[:5]
        if re.search(r"pon\W*sub", label):
            return DAYS[:6]
        if re.search(r"pon\W*čet", label):
            return DAYS[:4]
        if re.search(r"pon.*sri.*pet", label):
            return ["Mo", "We", "Fr"]
        if re.search(r"utor.*četv", label):
            return ["Tu", "Th"]
        for word, day in (("utorkom", "Tu"), ("srijedom", "We"), ("četvrtkom", "Th")):
            if word in label:
                return [day]
        if re.fullmatch(r"\W*sub(ota)?\W*", label):
            return ["Sa"]
        if re.fullmatch(r"\W*pet\W*", label):
            return ["Fr"]
        return None
