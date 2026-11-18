import re
from datetime import datetime
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The page spells some states out and abbreviates others.
STATES = {"Indiana": "IN", "Kentucky": "KY", "Michigan": "MI", "Ohio": "OH", "Pennsylvania": "PA"}
# One address carries its unit on the city line rather than the street line.
UNIT = re.compile(r"^(?P<unit>(?:Suite|Ste\.?|Space|Unit|#)\s*\S+)\s+(?P<city>.+)$", re.IGNORECASE)
STATE_POSTCODE = re.compile(r"^(?P<state>.+?)\s+(?P<postcode>\d{5})$")
HOURS = re.compile(
    r"(?P<days>[A-Z]+(?:\s*-\s*[A-Z]+)?)\s+(?P<open>\d{1,2}:\d{2}\s*[ap]m)\s*-\s*(?P<close>\d{1,2}:\d{2}\s*[ap]m)",
    re.IGNORECASE,
)


class TheEagleUSSpider(Spider):
    name = "the_eagle_us"
    item_attributes = {"brand": "The Eagle"}
    start_urls = ["https://www.eaglerestaurant.com/locations/"]

    @staticmethod
    def lines(markup: str) -> list[str]:
        """Return the address block's lines, which <br> separates rather than elements."""
        parts = re.split(r"<br[^>]*>", markup)
        parts = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", part)).strip() for part in parts]
        return [part for part in parts if part]

    @staticmethod
    def normalise(time: str) -> str:
        return datetime.strptime(re.sub(r"\s+", "", time).upper(), "%I:%M%p").strftime("%H:%M")

    def hours(self, lines: list[str]) -> OpeningHours:
        oh = OpeningHours()
        for line in lines:
            if not (match := HOURS.search(line)):
                continue
            opens, closes = self.normalise(match["open"]), self.normalise(match["close"])
            if closes == "00:00":
                # These kitchens close at midnight rather than opening for a minute.
                closes = "24:00"
            labels = re.split(r"\s*-\s*", match["days"])
            if len(labels) == 2 and (start := sanitise_day(labels[0])) and (end := sanitise_day(labels[1])):
                days = day_range(start, end)
            else:
                days = [day] if (day := sanitise_day(labels[0])) else []
            for day in days:
                oh.add_range(day, opens, closes)
        return oh

    def address(self, item: Feature, lines: list[str]) -> None:
        street, locality = lines[0].rstrip(" ,"), lines[-1]
        city, _, tail = locality.rpartition(",")
        if unit := UNIT.match(city.strip()):
            # "Suite G112 Mason, Ohio 45040" names the unit, then the city.
            street = f"{street}, {unit['unit']}"
            city = unit["city"]
        # One city is misspelt at source with a second capital ("PIttsburgh").
        city = re.sub(r"\b([A-Z])([A-Z])(?=[a-z])", lambda m: m[1] + m[2].lower(), city.strip())

        item["street_address"] = street
        item["city"] = city
        if match := STATE_POSTCODE.match(tail.strip()):
            state = match["state"]
            if len(state) > 2 and not (state := STATES.get(state)):
                self.logger.warning(f"Unmapped state in {locality!r}")
            item["state"] = state
            item["postcode"] = match["postcode"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for card in response.xpath('//div[@class="card"]'):
            item = Feature()
            item["branch"] = (card.xpath(".//h2/text()").get() or "").strip() or None
            item["ref"] = item["branch"]
            item["website"] = response.url
            item["phone"] = card.xpath('.//a[starts-with(@href, "tel:")]/@href').re_first(r"tel:(.+)")

            if address := card.xpath(".//address/a").get():
                if len(lines := self.lines(address)) >= 2:
                    self.address(item, lines)

            item["opening_hours"] = self.hours(card.xpath('.//ul[contains(@class, "list-hours")]/li/text()').getall())

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "american"
            yield item
