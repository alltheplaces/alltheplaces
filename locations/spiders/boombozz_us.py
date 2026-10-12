import re
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page carries the addresses, coordinates and Google place ids in
# a "locations" JavaScript array, and the phone and hours in the matching
# article cards, paired by their order on the page.
#
# The hours are free text and differ per restaurant: "Sun - Thur | 11am - 10pm"
# and "Fri - Sat 11 a.m. - 11 p.m." both appear.
#
# No brand:wikidata is set because the chain has no Wikidata item.

PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class BoombozzUSSpider(Spider):
    name = "boombozz_us"
    item_attributes = {"brand": "BoomBozz Craft Pizza & Taphouse"}
    allowed_domains = ["boombozz.com"]
    start_urls = ["https://boombozz.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if not (locations := re.search(r"(?:var|const|let)\s+locations\s*=\s*", response.text)):
            self.logger.error("No locations on the locations page")
            return

        cards = response.xpath("//article")

        for index, location in enumerate(chompjs.parse_js_object(response.text[locations.end() :])):
            address = location.get("address") or {}

            item = Feature()
            item["ref"] = address.get("addressable_id") or address.get("id")
            item["branch"] = location.get("title")
            item["street_address"] = ", ".join(
                part for part in [address.get("street"), address.get("street_two")] if part
            )
            item["city"] = address.get("city")
            item["state"] = address.get("state")
            item["postcode"] = address.get("zip")
            item["country"] = address.get("country")
            item["lat"] = address.get("lat")
            item["lon"] = address.get("lng")
            if place_id := location.get("place_id") or address.get("place_id"):
                item["extras"]["ref:google:place_id"] = place_id

            if index < len(cards):
                lines = [
                    re.sub(r"\s+", " ", line).strip()
                    for line in cards[index].xpath(".//text()").getall()
                    if line.strip()
                ]
                if phone := next((PHONE.fullmatch(line) for line in lines if PHONE.fullmatch(line)), None):
                    item["phone"] = phone.group(0)
                item["opening_hours"] = self.parse_opening_hours(lines)

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "pizza"

            yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """The hours read "Sun - Thur | 11am - 10pm" or "Fri - Sat 11 a.m. - 11 p.m."."""
        oh = OpeningHours()

        for line in lines:
            line = line.replace("\u2013", "-").replace("|", " ").replace("&", "-")
            line = re.sub(r"(?i)([ap])\.m\.", r"\1m", line)
            if not (times := re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", line, re.I)):
                continue

            days = []
            for part in re.split(r",|\band\b", line[: times.start()]):
                tokens = [day for token in part.split("-") if (day := sanitise_day(token.strip(" :|")))]
                if len(tokens) == 2:
                    days.extend(day_range(tokens[0], tokens[1]))
                else:
                    days.extend(tokens)

            if not days:
                continue

            oh.add_days_range(
                days,
                BoombozzUSSpider.normalise_time(times.group(1)),
                BoombozzUSSpider.normalise_time(times.group(2)),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
