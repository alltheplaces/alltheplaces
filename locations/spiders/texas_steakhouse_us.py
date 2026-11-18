import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The one site serves both of the operator's brands, naming the brand on each
# location's own page, so each POI is attributed from what its page says.
BRANDS = ("Texas Steakhouse & Saloon", "Sagebrush Steakhouse")
ADDRESS = re.compile(r"^(?P<street>.+?),\s*(?P<city>[^,]+),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5})$")
PHONE = re.compile(r"^\d{3}-\d{3}-\d{4}$")
TIME_RANGE = re.compile(r"(\d{1,2}(?::\d{2})?[AP]M)\s*[-–]\s*(\d{1,2}(?::\d{2})?[AP]M)", re.IGNORECASE)


class TexasSteakhouseUSSpider(Spider):
    name = "texas_steakhouse_us"
    start_urls = ["https://texassteakhouse.com/locations/"]

    @staticmethod
    def lines(markup: str) -> list[str]:
        """Return the block's visible lines, which <br> separates rather than elements."""
        parts = re.split(r"<br[^>]*>", markup)
        parts = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", part)).strip() for part in parts]
        return [part for part in parts if part]

    @staticmethod
    def days(spec: str) -> list[str]:
        """Resolve a day label such as "Sun-Thurs", "Fri-Sat" or "7 Days a Week"."""
        spec = spec.strip(" ,:")
        if re.search(r"(?i)7 days|daily|every ?day", spec):
            return [sanitise_day(day) for day in DAYS_FULL]
        if len(parts := re.split(r"\s*[-–]\s*", spec)) == 2:
            if (start := sanitise_day(parts[0])) and (end := sanitise_day(parts[1])):
                return day_range(start, end)
        return [day] if (day := sanitise_day(spec)) else []

    def hours(self, markup: str) -> OpeningHours:
        oh = OpeningHours()
        for line in self.lines(markup):
            if not (times := TIME_RANGE.search(line)):
                continue
            opens, closes = (time if ":" in time else time[:-2] + ":00" + time[-2:] for time in times.groups())
            # Rocky Mount labels its breakfast service rather than its days, and
            # states the days after the times instead: "6:30AM-10AM, 7 Days a Week".
            for day in self.days(line[: times.start()]) or self.days(line[times.end() :]):
                oh.add_range(day, opens, closes, time_format="%I:%M%p")
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        # The location cards carry no links of their own, so the pages are reached
        # from the nav, and the cards are read only for the coordinates some hold.
        coordinates = {}
        for title, block in re.findall(r"<h4>((?:Texas|Sagebrush)[^<]*)</h4>\s*<p>(.*?)</p>", response.text, re.S):
            city = re.sub(r"(?i)^(?:texas|sagebrush)\s+", "", title).strip().lower().replace(" ", "-")
            for link in re.findall(r'href="([^"]*maps[^"]*)"', block):
                # A directions link pins the destination as "!1d<lon>!2d<lat>" and
                # otherwise only centres the map on it as "@<lat>,<lon>".
                if pin := re.search(r"!1d(-?\d+\.\d+)!2d(-?\d+\.\d+)", link):
                    coordinates[city] = (pin.group(2), pin.group(1))
                elif centre := re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", link):
                    coordinates.setdefault(city, centre.groups())

        for url in response.xpath('//a[re:test(@href, "/[a-z-]+-(nc|wv)/$")]/@href').getall():
            slug = url.rstrip("/").rsplit("/", 1)[-1]
            city = re.sub(r"-(?:nc|wv)$", "", slug)
            yield response.follow(url, callback=self.parse_location, cb_kwargs={"coordinates": coordinates.get(city)})

    def parse_location(self, response: Response, coordinates: tuple | None) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        item["website"] = response.url

        welcome = response.xpath('//h4[contains(., "Welcome to")]//text()').get("")
        if not (brand := next((name for name in BRANDS if name in welcome), None)):
            self.logger.warning(f"Unrecognised brand on {response.url}: {welcome!r}")
            return
        item["brand"] = brand
        heading = response.xpath('//h4[contains(., "Welcome to")]/following::h1[1]//text()').get("")
        item["branch"] = heading.split(",")[0].strip() or None

        details = [
            re.sub(r"\s+", " ", text).strip()
            for text in response.xpath('//h4[contains(@style, "font-size: 24px")]//text()').getall()
        ]
        for detail in details:
            if address := ADDRESS.match(detail):
                item.update(
                    {
                        "street_address": address["street"],
                        "city": address["city"],
                        "state": address["state"],
                        "postcode": address["postcode"],
                    }
                )
                break
        item["phone"] = next((detail for detail in details if PHONE.match(detail)), None)

        if embed := response.xpath('//iframe[contains(@src, "google.com/maps/embed")]/@src').get():
            if pin := re.search(r"!2d(-?\d+\.\d+)!3d(-?\d+\.\d+)", embed):
                coordinates = (pin.group(2), pin.group(1))
        if coordinates:
            item["lat"], item["lon"] = coordinates

        if hours := response.xpath('//h2[contains(., "Hours")]/following::h4[1]').get():
            item["opening_hours"] = self.hours(hours)

        # Only the pages that advertise a patio are taken to have one; the rest say
        # nothing either way, so nothing is claimed for them.
        if any("Outdoor Seating" in detail for detail in details):
            apply_yes_no("outdoor_seating", item, True)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "steak_house"
        yield item
