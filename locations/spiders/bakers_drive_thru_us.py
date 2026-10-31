import html
import json
import re
from collections import Counter
from datetime import datetime
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

LOCATIONS = re.compile(r"var locations\s*=\s*(\[.*?\]);", re.DOTALL)
DAY = "|".join(DAYS_FULL)
TIME = r"\d{1,2}(?::\d{2})?\s*[AP]M"
HOURS = re.compile(
    rf"(?P<days>(?:{DAY})(?:\s*(?:[-–]|to|through|&|and)\s*(?:{DAY}))?)\s*:\s*"
    rf"(?P<opens>{TIME})\s*[-–]\s*(?P<closes>{TIME})",
    re.IGNORECASE,
)
# An address ends with its city, state and postcode. Its lines are separated by
# newlines on all but one record, which runs the street and city together.
LOCALITY = re.compile(r"^(?P<head>.*),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5})$", re.DOTALL)


class BakersDriveThruUSSpider(Spider):
    name = "bakers_drive_thru_us"
    item_attributes = {"brand": "Baker's Drive Thru", "brand_wikidata": "Q4849073"}
    start_urls = ["https://www.bakersdrivethru.com/find-a-location/"]

    @staticmethod
    def normalise(time: str) -> str:
        time = re.sub(r"\s+", "", time).upper()
        return datetime.strptime(time, "%I:%M%p" if ":" in time else "%I%p").strftime("%H:%M")

    def hours(self, availability: str) -> OpeningHours:
        oh = OpeningHours()
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", availability or "")))
        for match in HOURS.finditer(text):
            labels = re.split(r"\s*(?:[-–]|to|through|&|and)\s*", match["days"], flags=re.IGNORECASE)
            days = [day for label in labels if (day := sanitise_day(label))]
            if len(days) == 2:
                days = day_range(*days)
            closes = self.normalise(match["closes"])
            if closes == "00:00":
                # These restaurants close at midnight rather than opening for a minute.
                closes = "24:00"
            for day in days:
                oh.add_range(day, self.normalise(match["opens"]), closes)
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        locations = json.loads(LOCATIONS.search(response.text).group(1))

        # One pair of coordinates is published for two different restaurants, so it
        # cannot describe both and is not used for either.
        shared = {pin for pin, count in Counter(self.pin(entry) for entry in locations).items() if count > 1}

        for entry in locations:
            item = Feature()
            # The titles are not unique: nine of them name more than one restaurant.
            item["branch"] = entry.get("title")
            item["website"] = entry.get("permalink")
            item["ref"] = (entry.get("permalink") or "").rstrip("/").rsplit("/", 1)[-1] or None

            self.address(item, entry)

            # The numbers are wrapped in Unicode directional overrides, which are
            # invisible but would be published as part of the number.
            if phone := entry.get("phone"):
                item["phone"] = re.sub(r"[‪-‮‎‏]", "", phone).strip()

            if (pin := self.pin(entry)) and pin not in shared:
                item["lat"], item["lon"] = pin

            item["opening_hours"] = self.hours(entry.get("availability"))

            apply_category(Categories.FAST_FOOD, item)
            apply_yes_no("drive_through", item, True)
            item["extras"]["cuisine"] = "burger;mexican"
            yield item

    def address(self, item: Feature, entry: dict) -> None:
        if not (match := LOCALITY.match((entry.get("address") or "").strip())):
            self.logger.warning(f"Unparsed address: {entry.get('address')!r}")
            return
        item["state"] = match["state"]
        item["postcode"] = match["postcode"]

        lines = [line.strip() for line in re.split(r"[\r\n]+", match["head"]) if line.strip()]
        if len(lines) > 1:
            item["city"] = lines[-1]
            item["street_address"] = merge_address_lines(lines[:-1])
        elif (title := (entry.get("title") or "").strip()) and lines[0].endswith(title):
            # The one run-together address ends with the city the record is titled by.
            item["city"] = title
            item["street_address"] = lines[0][: -len(title)].strip(" ,")
        else:
            self.logger.warning(f"Unseparated address: {entry.get('address')!r}")
            item["street_address"] = lines[0]

    @staticmethod
    def pin(entry: dict) -> tuple[str, str] | None:
        """Return a record's coordinates, in the order they were meant to be given.

        One record has its latitude and longitude the wrong way round, which a
        latitude beyond the poles gives away.
        """
        latitude, longitude = entry.get("latitude"), entry.get("longitude")
        if not latitude or not longitude:
            return None
        try:
            if abs(float(latitude)) > 90:
                latitude, longitude = longitude, latitude
        except ValueError:
            return None
        return latitude, longitude
