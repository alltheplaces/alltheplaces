import json
import re
from itertools import groupby
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_WEEKDAY, OpeningHours
from locations.items import Feature

OPERATOR = {"operator": "Åland Post", "operator_wikidata": "Q1951188"}

# Swedish day names as used in the letter box collection times ("tömning").
DAYS_AX = {
    "mån": "Mo",
    "må": "Mo",
    "tis": "Tu",
    "ti": "Tu",
    "ons": "We",
    "on": "We",
    "tor": "Th",
    "to": "Th",
    "fre": "Fr",
    "fr": "Fr",
    "lör": "Sa",
    "sön": "Su",
}
DAY_TOKEN = r"(?:vardagar|mån\w*|må|tis\w*|ti|ons\w*|on|tor\w*|to|fre\w*|fr|lör\w*|sön\w*)"


def next_flight_data(html: str) -> str:
    """Concatenate the Next.js React Server Components payload embedded in the page."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', html)
    return "".join(json.loads(chunk) for chunk in chunks)


def json_array(data: str, key: str) -> list:
    start = data.find(f'"{key}":[')
    if start < 0:
        return []
    return json.JSONDecoder().raw_decode(data, start + len(key) + 3)[0]


def to_day(token: str) -> str | None:
    token = token.lower().rstrip(".")
    for prefix, day in DAYS_AX.items():
        if token.startswith(prefix):
            return day
    return None


def parse_collection_times(text: str) -> str:
    # "Vardagar 14:00, Lördagar 11:00", "Vardagar Månd.12:30 Tisd-Fred. 15:00",
    # "Vardagar Må,On,Fr 10:00  Ti,To 9:00", "Vardagar 12:00 o 16:30 Måndagar också 07:30"
    text = re.sub(r"(\d) (\d:\d\d)", r"\1\2", text)  # "Månd.1 3:00"
    times: dict[str, set[str]] = {}
    days: list[str] = []
    pending: list[str] = []  # day names collected since the last time
    in_range = False
    for token in re.findall(rf"\d{{1,2}}[:.]\d{{2}}|(?<![a-zåäö]){DAY_TOKEN}(?![a-zåäö])|-", text, re.I):
        if token == "-":
            in_range = bool(pending)
        elif re.match(r"\d", token):
            if pending:
                days, pending = pending, []
            for day in days or DAYS_WEEKDAY:
                times.setdefault(day, set()).add(token.replace(".", ":").zfill(5))
        elif token.lower() == "vardagar":
            pending = list(DAYS_WEEKDAY)
        elif day := to_day(token):
            if in_range and pending:
                pending = pending + DAYS[DAYS.index(pending[-1]) + 1 : DAYS.index(day) + 1]
            else:
                pending = pending + [day] if pending and not days_complete(pending) else [day]
            in_range = False
    by_day = {day: ",".join(sorted(t)) for day, t in times.items()}
    out = []
    for time, group in groupby(DAYS, key=by_day.get):
        if time:
            group = list(group)
            out.append(f"{group[0]}-{group[-1]} {time}" if len(group) > 2 else f"{','.join(group)} {time}")
    return "; ".join(out)


def days_complete(pending: list[str]) -> bool:
    # "Vardagar" followed by an explicit day starts a new group rather than extending Mo-Fr.
    return pending == DAYS_WEEKDAY


class AlandPostAxSpider(Spider):
    name = "aland_post_ax"
    allowed_domains = ["www.alandpost.ax"]
    # Both pages are Next.js; the letter boxes (with collection times) and the post offices and
    # postal agents (with coordinates) are embedded in the server components payload.

    async def start(self) -> AsyncIterator[Request]:
        yield Request("https://www.alandpost.ax/en/post-offices-and-agents", callback=self.parse_boxes)
        yield Request("https://www.alandpost.ax/en/post-offices-and-agents/map", callback=self.parse_offices)

    def parse_boxes(self, response: Response) -> Any:
        for box in json_array(next_flight_data(response.text), "mailboxes"):
            item = Feature(**OPERATOR)
            item["ref"] = str(box["id"])
            item["lat"], item["lon"] = box["latitude"], box["longitude"]
            item["postcode"] = str(box.get("postnr") or "")
            item["country"] = "AX"
            if location := (box.get("placering") or "").strip():
                item["extras"]["description"] = location
            if collection_times := parse_collection_times(box.get("tomning") or ""):
                item["extras"]["collection_times"] = collection_times
            apply_category(Categories.POST_BOX, item)
            yield item

    def parse_offices(self, response: Response) -> Any:
        data = next_flight_data(response.text)
        for key in ("postOffices", "postalAgents"):
            for place in json_array(data, key):
                if not place.get("location"):
                    continue
                blocks = self.blocks(place.get("content") or [])
                item = Feature()
                item["ref"] = place["_id"]
                item["lat"], item["lon"] = place["location"]["lat"], place["location"]["lng"]
                item["country"] = "AX"
                postcode, _, city = (place.get("heading") or "").partition(" ")
                item["postcode"], item["city"] = postcode, city
                item["street_address"] = blocks.get("Visiting Address")
                phone = re.search(r"\+[\d ]{6,}", blocks.get("Telephone", ""))
                if phone and len(re.sub(r"\D", "", phone.group(0))) >= 8:
                    item["phone"] = phone.group(0).strip()
                oh = OpeningHours()
                oh.add_ranges_from_string(blocks.get("Opening Hours", "").replace("Saturday–Sunday: Closed", ""))
                item["opening_hours"] = oh
                sub_heading = (place.get("subHeading") or "").strip()
                if key == "postOffices":
                    item.update(OPERATOR)
                    item["branch"] = sub_heading or city
                    apply_category(Categories.POST_OFFICE, item)
                else:
                    # Postal agents are post counters run by local shops and hotels; on some islands
                    # Åland Post's own rural mail carrier acts as the service point.
                    if sub_heading.lower() == "rural mail carrier":
                        item.update(OPERATOR)
                        item["extras"]["description"] = sub_heading
                    else:
                        item["name"] = re.sub(r"^Postal Agent,\s*", "", sub_heading) or None
                    item["extras"]["post_office"] = "post_partner"
                    item["extras"]["post_office:brand"] = OPERATOR["operator"]
                    item["extras"]["post_office:brand:wikidata"] = OPERATOR["operator_wikidata"]
                    apply_category(Categories.GENERIC_POI, item)
                yield item

    @staticmethod
    def blocks(content: list[dict]) -> dict[str, str]:
        # Portable Text blocks of the form "<strong>Label:</strong> value"
        out = {}
        for block in content:
            spans = block.get("children") or []
            if spans and "strong" in (spans[0].get("marks") or []):
                label = spans[0].get("text", "").strip().rstrip(":")
                out.setdefault(label, "".join(s.get("text", "") for s in spans[1:]).strip())
        return out
