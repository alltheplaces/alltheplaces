import re
from typing import Any, AsyncIterator

from scrapy import Request, Spider
from scrapy.http import Response

from locations.hours import DAYS_FR, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines


class G20FRSpider(Spider):
    name = "g20_fr"
    item_attributes = {"brand": "G20", "brand_wikidata": "Q3504731"}

    async def start(self) -> AsyncIterator[Request]:
        # The store finder only returns the 200 stores nearest to a point.
        for lat, lon in [(48.86, 2.35), (48.11, -1.68), (44.84, -0.58), (43.3, 3.0), (45.76, 4.84), (50.63, 3.06)]:
            yield Request(f"https://www.supermarchesg20.com/nos-magasins?lat={lat}&lng={lon}")

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for url in response.css(".list-store .store-data a::attr(href)").getall():
            yield response.follow(url, self.parse_store)

    def parse_store(self, response: Response) -> Any:
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url

        label = response.css("#store_adresse .label-section::text").get("").strip().removeprefix("Supermarché G20")
        if branch := re.sub(r"^\s*(SUPERMA?R?CHE\s+)?G20\b", "", label).strip(" -"):
            item["branch"] = branch

        street_lines = []
        for line in response.css("#store_adresse .info::text").getall():
            line = line.strip()
            if line.startswith("Téléphone"):
                item["phone"] = line.partition(":")[2].split("- Fax")[0].strip()
            elif m := re.fullmatch(r"(\d{5})\s+(.+)", line):
                item["postcode"] = m.group(1)
                item["city"] = re.sub(r"\s+\d{1,2}(ER|EME)$", "", m.group(2), flags=re.IGNORECASE)
            elif line:
                street_lines.append(line)
        item["street_address"] = merge_address_lines(street_lines)

        if coords := response.xpath("//script/text()").re(
            r"position:\s*new google\.maps\.LatLng\(\s*(-?[\d.]+),\s*(-?[\d.]+)"
        ):
            item["lat"], item["lon"] = coords[0], coords[1]

        hours = " ".join(response.css("#store_horaire .info::text").getall()).lower().replace("minuit", "00h")
        hours = re.sub(r"(\d{1,2})h(\d{2})?", lambda m: f"{int(m.group(1)):02d}:{m.group(2) or '00'}", hours)
        closed_days = [
            day for word in re.findall(r"fermé\s+(?:le\s+)?([a-zé]+)", hours) if (day := sanitise_day(word, DAYS_FR))
        ]
        hours = re.sub(r"fermé\s+(?:le\s+)?[a-zé]+", "", hours)
        # Free text, e.g. "Du lundi au jeudi de 8h30 à 13h et de 14h30 à 19h30, le vendredi et le samedi de 8h30
        # à 19h30, le dimanche dès 9h": time ranges apply to the days named since the previous ones, and a day
        # named again later overrides them. Open-ended times ("dès", "à partir de") are skipped.
        ranges, days, days_done = {}, [], False
        for m in re.finditer(
            r"(?:du\s+)?(?P<first>[a-zé]+)(?:\s+au\s+|\s*-\s*)(?P<last>[a-zé]+)|(?P<day>[a-zé]+)"
            r"|(?P<open>\d\d:\d\d)\s*à\s*(?P<close>\d\d:\d\d)",
            hours,
        ):
            if m["open"]:
                for day in days:
                    if not days_done:
                        ranges[day] = []
                    ranges[day].append((m["open"], m["close"]))
                days_done = True
                continue
            if m["first"]:
                first, last = sanitise_day(m["first"], DAYS_FR), sanitise_day(m["last"], DAYS_FR)
                new_days = day_range(first, last) if first and last else [d for d in (first, last) if d]
            else:
                new_days = [d] if (d := sanitise_day(m["day"], DAYS_FR)) else []
            if new_days:
                if days_done:
                    days, days_done = [], False
                days += new_days
        oh = OpeningHours()
        for day, day_ranges in ranges.items():
            if day not in closed_days:
                for open_time, close_time in day_ranges:
                    oh.add_range(day, open_time, close_time)
        oh.set_closed(closed_days)
        item["opening_hours"] = oh

        yield item
