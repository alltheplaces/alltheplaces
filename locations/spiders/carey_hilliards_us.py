import html
import re
from datetime import datetime
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FULL, OpeningHours, day_range, sanitise_day
from locations.items import Feature

DAY = r"Daily|Everyday|Every Day|Mon|Tues?|Wed|Thur?s?|Fri|Sat|Sun" + "".join(f"|{day}" for day in DAYS_FULL)
TIME = r"\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?|Midnight|Noon"
HOURS = re.compile(
    rf"(?:Open\s+)?(?P<days>(?:{DAY})(?:\s*(?P<joiner>[-–]|&|and|through|to)\s*(?:{DAY}))?)\s*:?\s*"
    rf"(?P<opens>{TIME})\s*(?:[-–]|to|til|till|'til)\s*(?P<closes>{TIME})",
    re.IGNORECASE,
)
LOCALITY = re.compile(r"^(?P<city>[A-Za-z .'/-]+),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5})$")
PHONE = re.compile(r"^Phone:\s*(?P<phone>.+)$", re.IGNORECASE)


class CareyHilliardsUSSpider(Spider):
    name = "carey_hilliards_us"
    item_attributes = {"brand": "Carey Hilliard's"}
    start_urls = ["https://careyhilliards.com/locations/"]

    @staticmethod
    def lines(markup: str) -> list[str]:
        """Return a block's visible lines, which <br> separates rather than elements."""
        parts = re.split(r"<br[^>]*>", markup)
        parts = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", part))).strip() for part in parts]
        return [part for part in parts if part]

    @staticmethod
    def normalise(time: str) -> str:
        if re.fullmatch(r"(?i)midnight", time):
            return "24:00"
        if re.fullmatch(r"(?i)noon", time):
            return "12:00"
        time = re.sub(r"[\s.]", "", time).upper()
        return datetime.strptime(time, "%I:%M%p" if ":" in time else "%I%p").strftime("%H:%M")

    def hours(self, text: str) -> OpeningHours:
        oh = OpeningHours()
        for match in HOURS.finditer(text):
            labels = re.split(r"\s*(?:[-–]|&|and|through|to)\s*", match["days"], flags=re.IGNORECASE)
            if re.fullmatch(r"(?i)daily|everyday|every day", labels[0]):
                days = [sanitise_day(day) for day in DAYS_FULL]
            else:
                days = [day for label in labels if (day := sanitise_day(label))]
                if len(days) == 2 and match["joiner"] not in ("&", "and"):
                    days = day_range(*days)
            for day in days:
                oh.add_range(day, self.normalise(match["opens"]), self.normalise(match["closes"]))
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        urls = set(response.xpath('//a[re:test(@href, "/locations/[^/]+/$")]/@href').getall())
        for url in urls:
            yield response.follow(url, callback=self.parse_location)

    def parse_location(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        heading = response.xpath('normalize-space(//h1[contains(@class, "fl-heading")])').get("")
        if re.search(r"(?i)banquet hall", heading):
            # An events space behind one of the restaurants, sharing its street
            # address, so it is not a restaurant POI of its own.
            return

        details = []
        for block in response.xpath('//div[contains(@class, "fl-rich-text")]//p').getall():
            lines = self.lines(block)
            if any(PHONE.match(line) for line in lines):
                details = lines
                break

        item = Feature()
        item["ref"] = item["website"] = response.url
        # The restaurants are distinguished by the chain's own short names for them,
        # which each page gives on its ordering button.
        if label := response.xpath('//span[contains(@class, "fl-button-text")]/text()').re_first(
            r"(?i)order online at\s+(.+)"
        ):
            item["branch"] = label.strip().title()

        for line in details:
            if address := LOCALITY.match(line):
                item["city"] = address["city"]
                item["state"] = address["state"]
                item["postcode"] = address["postcode"]
            elif match := PHONE.match(line):
                item["phone"] = match["phone"]
            elif re.match(r"^\d+\s", line) and not item.get("street_address"):
                item["street_address"] = line

        item["opening_hours"] = self.hours(" ".join(details))

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "barbecue;seafood"
        yield item
