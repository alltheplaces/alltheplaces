import html
import re
from datetime import datetime
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category, apply_yes_no
from locations.hours import DAYS_FULL, OpeningHours, day_range, sanitise_day
from locations.items import Feature

DAY = r"Mon|Tues?|Wed|Thur?s?|Fri|Sat|Sun" + "".join(f"|{day}" for day in DAYS_FULL)
TIME = r"\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?"
# The listing writes a whole week on one line as "Sun-Thurs 11am-8pm; Fri-Sat
# 11am-9pm", while a location's own page labels each range as "Sunday – Thursday"
# above its times. Joined up, both read the same way.
HOURS = re.compile(
    rf"(?P<days>(?:{DAY})(?:\s*(?P<joiner>[-–]|&|and|through)\s*(?:{DAY}))?)\s*:?\s*"
    rf"(?P<opens>{TIME})\s*(?:[-–]|to)\s*(?P<closes>{TIME})",
    re.IGNORECASE,
)
ADDRESS = re.compile(
    r"^(?:(?P<street>.+?),\s*)?(?P<city>[A-Za-z .'/-]+),\s*(?P<state>[A-Za-z]{2}),?\s+(?P<postcode>\d{5})$"
)
PHONE = re.compile(r"^(?:P:\s*)?(?P<phone>\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4})$")
COORDINATES = re.compile(r"!2d(?P<lon>-?\d+\.\d+)!3d(?P<lat>-?\d+\.\d+)")


class PicazzosUSSpider(Spider):
    name = "picazzos_us"
    item_attributes = {"brand": "Picazzo's Healthy Italian Kitchen"}
    start_urls = ["https://picazzos.com/locations/"]

    @staticmethod
    def lines(markup: str) -> list[str]:
        """Return a block's visible lines, which <br> separates rather than elements."""
        parts = re.split(r"<br[^>]*>", markup)
        parts = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", part))).strip() for part in parts]
        return [part for part in parts if part]

    @staticmethod
    def normalise(time: str) -> str:
        time = re.sub(r"[\s.]", "", time).upper()
        return datetime.strptime(time, "%I:%M%p" if ":" in time else "%I%p").strftime("%H:%M")

    def hours(self, text: str) -> OpeningHours:
        oh = OpeningHours()
        for match in HOURS.finditer(text):
            labels = re.split(r"\s*(?:[-–]|&|and|through)\s*", match["days"], flags=re.IGNORECASE)
            days = [day for label in labels if (day := sanitise_day(label))]
            if len(days) == 2 and match["joiner"] not in ("&", "and"):
                days = day_range(*days)
            for day in days:
                oh.add_range(day, self.normalise(match["opens"]), self.normalise(match["closes"]))
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Any]:
        for card in response.xpath('//div[contains(@class, "wp-block-media-text__content")][.//h4]'):
            paragraphs = [self.lines(paragraph) for paragraph in card.xpath(".//p").getall()]
            yield response.follow(
                card.xpath('.//a[contains(@class, "wp-block-button__link")]/@href').get(),
                callback=self.parse_location,
                cb_kwargs={
                    "branch": card.xpath("normalize-space(.//h4)").get(),
                    # The listing's address and hours are the better copy: a location's
                    # own page breaks street lines mid-name ("8280 W. Union Hills," then
                    # "Dr. Glendale, AZ 85308") and gives one location Sunday hours that
                    # the listing contradicts.
                    "lines": [line for paragraph in paragraphs for line in paragraph],
                },
            )

    def parse_location(self, response: Response, branch: str, lines: list[str]) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = item["website"] = response.url
        item["branch"] = branch

        # Only this location's own page states its phone and hours.
        fallback = [
            line
            for paragraph in response.xpath(
                '//div[contains(@class, "wp-block-media-text__content")][.//h2]//p'
            ).getall()
            for line in self.lines(paragraph)
        ]

        for source in (lines, fallback):
            for line in source:
                if address := ADDRESS.match(line):
                    item["street_address"] = address["street"] or item.get("street_address")
                    item["city"] = address["city"]
                    item["state"] = address["state"].upper()
                    item["postcode"] = address["postcode"]
                elif re.match(r"^\d+\s", line) and not item.get("street_address"):
                    item["street_address"] = line
            if item.get("city"):
                break

        item["phone"] = next(
            (match["phone"] for line in lines + fallback if (match := PHONE.match(line))),
            None,
        )

        hours = self.hours(" ".join(lines)) or self.hours(" ".join(fallback))
        item["opening_hours"] = hours

        if pin := COORDINATES.search(response.text):
            item["lat"], item["lon"] = pin["lat"], pin["lon"]

        # One location states that it takes no reservations; the rest say nothing.
        if any("do not accept reservations" in line for line in lines + fallback):
            apply_yes_no("reservation", item, False, apply_positive_only=False)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "italian;pizza"
        yield item
