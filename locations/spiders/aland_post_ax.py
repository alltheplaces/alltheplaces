import json
import re
from itertools import groupby
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, DAYS_SE, NAMED_DAY_RANGES_SE, OpeningHours
from locations.items import Feature

OPERATOR = {"operator": "Åland Post", "operator_wikidata": "Q1951188"}

# Swedish day names and ranges ("Vardagar", "Månd.", "Tisd-Fred.") as matched by OpeningHours.
DAYS_REGEX = OpeningHours.any_day_extraction_regex(
    days=DAYS_SE, named_day_ranges=NAMED_DAY_RANGES_SE, delimiters=["-", "–"]
)
COLLECTION_TOKEN = re.compile(rf"(?P<days>{DAYS_REGEX})|(?P<time>\d{{1,2}}[:.]\d{{2}})|(?P<comma>,)", re.IGNORECASE)


def next_flight_data(html: str) -> str:
    """Concatenate the Next.js React Server Components payload embedded in the page."""
    chunks = re.findall(r'self\.__next_f\.push\(\[1,("(?:[^"\\]|\\.)*")\]\)', html)
    return "".join(json.loads(chunk) for chunk in chunks)


def json_array(data: str, key: str) -> list:
    start = data.find(f'"{key}":[')
    if start < 0:
        return []
    return json.JSONDecoder().raw_decode(data, start + len(key) + 3)[0]


def parse_collection_times(text: str) -> str:
    # "Vardagar 14:00, Lördagar 11:00", "Vardagar Månd.12:30 Tisd-Fred. 15:00",
    # "Vardagar Må,On,Fr 10:00  Ti,To 9:00", "Vardagar 12:00 o 16:30 Måndagar också 07:30"
    # Letter boxes have one collection time per day rather than an opening range, so OpeningHours
    # can't hold them; it still finds the day names, and each time applies to the days before it.
    text = re.sub(r"(\d) (\d:\d\d)", r"\1\2", text)  # "Månd.1 3:00"
    text = re.sub(r"(?<=[a-zåäö])\.", " ", text, flags=re.IGNORECASE)  # "Tisd.-Fred." -> "Tisd -Fred "
    times: dict[str, set[str]] = {}
    days: list[str] = []
    new_days = after_comma = False
    for token in COLLECTION_TOKEN.finditer(text):
        if token["days"]:
            day_range = [d for d in re.fullmatch(DAYS_REGEX, token["days"], re.IGNORECASE).groups() if d]
            matched = OpeningHours.days_in_day_range(day_range, DAYS_SE, NAMED_DAY_RANGES_SE)
            # "Må,On,Fr" adds to the days; "Vardagar Månd." or a day after a time starts afresh.
            days = days + matched if new_days and after_comma else matched
            new_days, after_comma = True, False
        elif token["comma"]:
            after_comma = True
        else:
            for day in days:
                times.setdefault(day, set()).add(token["time"].replace(".", ":").zfill(5))
            new_days = after_comma = False
    by_day = {day: ",".join(sorted(t)) for day, t in times.items()}
    out = []
    for time, group in groupby(DAYS, key=by_day.get):
        if time:
            group = list(group)
            out.append(f"{group[0]}-{group[-1]} {time}" if len(group) > 2 else f"{','.join(group)} {time}")
    return "; ".join(out)


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
