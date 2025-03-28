import re
from datetime import date, timedelta
from typing import Iterable
from urllib import parse as urlparse

from scrapy import Spider
from scrapy.http import Request, Response, TextResponse

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, DAYS_3_LETTERS, OpeningHours
from locations.items import Feature


def slugify(s: str) -> str:
    return re.sub(r"\s+", "-", s).casefold()


class NomNomSpider(Spider):
    """NomNom is an "accelerator technology" by Bounteous for restaurants and
    retailers:
    https://www.bounteous.com/industries/restaurant-convenience/nomnom/
    To use, specify "domain" as the base domain of the website."""

    domain: str | None = None
    use_calendar: bool = True

    def _append_calendar_param(self, url):
        if self.use_calendar:
            parsed = urlparse.urlparse(url)
            params = urlparse.parse_qs(parsed.query)
            today = date.today()
            params["nomnom"] = "calendars"
            params["nomnom_calendars_from"] = [today.strftime("%Y%m%d")]
            params["nomnom_calendars_to"] = [(today + timedelta(days=6)).strftime("%Y%m%d")]
            parsed = parsed._replace(query=urlparse.urlencode(params, doseq=True))
            return urlparse.urlunparse(parsed)
        else:
            return url

    def start_requests(self) -> Iterable[Request]:
        if self.start_urls:
            for url in self.start_urls:
                yield Request(self._append_calendar_param(url), dont_filter=True)
        elif self.domain:
            yield Request(self._append_calendar_param(f"https://nomnom-prod-api.{self.domain}/restaurants/"))

    @staticmethod
    def parse_opening_hours(calendar: dict) -> OpeningHours:
        oh = OpeningHours()
        for row in calendar["ranges"]:
            if row["weekday"] not in DAYS_3_LETTERS:
                continue
            day = DAYS[DAYS_3_LETTERS.index(row["weekday"])]
            oh.add_range(day, row["start"], row["end"], time_format="%Y%m%d %H:%M")
        return oh

    CALENDAR_KEYS = {
        "drivethru": "opening_hours:drive_through",
        "dispatch": "opening_hours:delivery",
    }

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json()["restaurants"]:
            item = DictParser.parse(location)
            item["ref"] = location["extref"]
            item["branch"] = location["name"].replace(location["storename"], "").strip()
            item["name"] = location["storename"]

            apply_yes_no(Extras.DELIVERY, item, location["candeliver"] or location["supportsdispatch"])
            apply_yes_no(Extras.TAKEAWAY, item, location["canpickup"] or location["supportscurbside"])
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["supportsdrivethru"])

            if self.use_calendar:
                calendars = location["calendars"]
                if isinstance(calendars, dict):
                    calendars = calendars["calendar"]
                if calendars is None:
                    calendars = []
                for calendar in calendars:
                    if calendar["type"] == "business":
                        item["opening_hours"] = self.parse_opening_hours(calendar)
                    elif key := self.CALENDAR_KEYS.get(calendar["type"]):
                        item["extras"][key] = self.parse_opening_hours(calendar).as_opening_hours()

            yield from self.post_process_item(item, response, location)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
