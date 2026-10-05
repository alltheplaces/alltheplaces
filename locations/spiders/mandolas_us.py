import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The locations page links to a page per restaurant, each listing the street,
# "city, state postcode", phone and hours as separate paragraphs.
#
# Those paragraphs are repeated for the desktop and mobile layouts, so only the
# first set is read.
#
# The hours are a sentence, e.g. "Open Every Day 11am - 9pm" or "Sun - Thu 11am
# - 9pm".
#
# No coordinates are published.
#
# No brand:wikidata is set because the chain has no Wikidata item.

# One restaurant writes its state as "Fl." rather than "FL".
ADDRESS = re.compile(r"(.+?),\s*([A-Za-z]{2})\.?\s+(\d{5})")
PHONE = re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")


class MandolasUSSpider(Spider):
    name = "mandolas_us"
    item_attributes = {"brand": "Mandola's Italian Kitchen"}
    allowed_domains = ["mandolas.com"]
    start_urls = ["https://mandolas.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for url in sorted(set(response.xpath("//a/@href").re(r"^https://mandolas\.com/locations/[a-z0-9-]+/$"))):
            yield response.follow(url, callback=self.parse_location)

    def parse_location(self, response: Response) -> Iterable[Feature]:
        lines = [
            re.sub(r"\s+", " ", " ".join(paragraph.xpath(".//text()").getall())).strip()
            for paragraph in response.xpath('//p[contains(@class, "vc_custom_heading")]')
        ]
        lines = [line for line in lines if line]

        locality = next((index for index, line in enumerate(lines) if ADDRESS.fullmatch(line)), None)
        if locality is None or locality == 0:
            return

        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[-1]
        # "Arbor Trails – Mandola's Italian Kitchen"
        item["branch"] = re.split(r"\s+[\u2013\u2014-]\s+", response.xpath("//title/text()").get("") or "")[0].strip()
        item["website"] = response.url
        item["street_address"] = lines[locality - 1]
        item["city"], state, item["postcode"] = ADDRESS.fullmatch(lines[locality]).groups()
        item["state"] = state.upper()

        # The paragraphs repeat for the desktop and mobile layouts.
        block = lines[locality : locality + 5]
        if phone := next((PHONE.fullmatch(line) for line in block if PHONE.fullmatch(line)), None):
            item["phone"] = phone.group(0)

        item["opening_hours"] = self.parse_opening_hours(block)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "italian"

        yield item

    @staticmethod
    def parse_opening_hours(lines: list[str]) -> OpeningHours | None:
        """The hours read "Open Every Day 11am - 9pm" or "Sun - Thu 11am - 9pm"."""
        oh = OpeningHours()

        for line in lines:
            line = line.replace("\u2013", "-").replace("\u2014", "-")
            if not (times := re.search(r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", line, re.I)):
                continue

            label = line[: times.start()]
            if re.search(r"(?i)every ?day|daily", label):
                days = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
            elif rule := re.search(r"([A-Za-z]{3,9})\s*-\s*([A-Za-z]{3,9})\s*$", label.strip(" :")):
                start, end = sanitise_day(rule.group(1)), sanitise_day(rule.group(2))
                if not start or not end:
                    continue
                days = day_range(start, end)
            elif day := sanitise_day(label.strip(" :")):
                days = [day]
            else:
                continue

            oh.add_days_range(
                days,
                MandolasUSSpider.normalise_time(times.group(1)),
                MandolasUSSpider.normalise_time(times.group(2)),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
