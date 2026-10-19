import html
import re
from datetime import datetime
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# The page abbreviates days to a single letter, which sanitise_day does not read.
# "T" is left out: on its own it is as much Tuesday as Thursday.
DAYS = {"M": "Mo", "W": "We", "F": "Fr"}
DAY = r"[MWF]|Tu|Th|Sa|Su|Mon|Tues?|Wed|Thur?s?|Fri|Sat|Sun"
TIME = r"\d{1,2}(?::\d{2})?\s*[ap]\.?m\.?"
HOURS = re.compile(
    rf"(?P<days>(?:{DAY})(?:\s*(?P<joiner>[-–]|&|and)\s*(?:{DAY}))?)\s*:\s*"
    rf"(?P<opens>{TIME})\s*[-–]\s*(?P<closes>{TIME})",
    re.IGNORECASE,
)
LOCALITY = re.compile(r"^(?P<city>[A-Za-z .'/-]+),\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5})$")


class CoolHandLukesUSSpider(Spider):
    name = "cool_hand_lukes_us"
    item_attributes = {"brand": "Cool Hand Luke's"}
    start_urls = ["https://coolhandlukes.com/locations/"]

    @staticmethod
    def lines(markup: str) -> list[str]:
        """Return a block's visible lines, which <br> separates rather than elements."""
        parts = re.split(r"<br[^>]*>", markup)
        parts = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", part))).strip() for part in parts]
        return [part for part in parts if part]

    @staticmethod
    def day(label: str) -> str | None:
        return DAYS.get(label.upper()) or sanitise_day(label)

    @staticmethod
    def normalise(time: str) -> str:
        time = re.sub(r"[\s.]", "", time).upper()
        return datetime.strptime(time, "%I:%M%p" if ":" in time else "%I%p").strftime("%H:%M")

    def hours(self, text: str) -> OpeningHours:
        oh = OpeningHours()
        for match in HOURS.finditer(text):
            labels = re.split(r"\s*(?:[-–]|&|and)\s*", match["days"], flags=re.IGNORECASE)
            days = [day for label in labels if (day := self.day(label))]
            if len(days) == 2 and match["joiner"] not in ("&", "and"):
                days = day_range(*days)
            for day in days:
                oh.add_range(day, self.normalise(match["opens"]), self.normalise(match["closes"]))
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # Only the innermost columns are location cards: an outer column wraps them
        # all and would otherwise be read as a further location of its own.
        columns = response.xpath(
            '//div[contains(@class, "wp-block-kadence-column")]'
            '[.//a[contains(@href, "goo.gl")]]'
            '[not(.//div[contains(@class, "wp-block-kadence-column")])]'
        )
        for column in columns:
            item = Feature()
            item["branch"] = column.xpath("normalize-space(.//h2)").get()
            item["ref"] = item["branch"]
            item["website"] = response.url
            item["phone"] = column.xpath('.//a[starts-with(@href, "tel:")]/text()').get()

            # The address sits in the block that links it to a map; the map links are
            # Google short links that resolve to an interstitial, so they give no
            # coordinates and the site publishes none anywhere else.
            address = column.xpath('.//*[a[contains(@href, "goo.gl")]]').get("")
            for line in self.lines(address):
                if locality := LOCALITY.match(line):
                    item["city"] = locality["city"]
                    item["state"] = locality["state"]
                    item["postcode"] = locality["postcode"]
                elif re.match(r"^\d+\s", line):
                    item["street_address"] = line

            # One location lists a Sunday brunch service below its regular hours,
            # which opens earlier than the Sunday range that follows it.
            hours = " ".join(
                line
                for block in column.xpath('.//*[contains(., "Hours:")]//text()').getall()
                for line in [re.sub(r"\s+", " ", html.unescape(block)).strip()]
                if line
            )
            item["opening_hours"] = self.hours(hours)

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "steak_house"
            yield item
