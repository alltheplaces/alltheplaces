import re
from datetime import date, timedelta
from typing import AsyncIterator, Iterable
from urllib import parse as urlparse

from scrapy import Spider
from scrapy.http import JsonResponse, Request

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, DAYS_3_LETTERS, OpeningHours
from locations.items import Feature


def slugify(s: str) -> str:
    return re.sub(r"\s+", "-", s).casefold()


class NomNomSpider(Spider):
    """
    NomNom is an "accelerator technology" by Bounteous for restaurants and
    retailers with an official website of:
    https://www.bounteous.com/industries/restaurant-convenience/nomnom/

    There are two ways this storefinder may be used.

    1. NomNom API with observed API requests to:
       https://nomnom-prod-api.example.net/restaurants/

       Specify the `domain` attribute of class to be "example.net".

    2. NomNom API with observed API requests to a custom URL.

       Specify the `start_urls` list attribute of this class to be a list
       with a single URL, for example,
       "https://api.storefinder.example.net/custom-path/restaurants"
    """

    domain: str | None = None
    start_urls: list[str] = []
    use_calendar: bool = True

    def _append_calendar_param(self, url: str) -> str:
        if self.use_calendar:
            parsed = urlparse.urlparse(url)
            params = dict(urlparse.parse_qs(parsed.query))
            today = date.today()
            params["nomnom"] = "calendars"
            params["nomnom_calendars_from"] = [today.strftime("%Y%m%d")]
            params["nomnom_calendars_to"] = [(today + timedelta(days=6)).strftime("%Y%m%d")]
            parsed = parsed._replace(query=urlparse.urlencode(params, doseq=True))
            return urlparse.urlunparse(parsed)
        else:
            return url

    async def start(self) -> AsyncIterator[Request]:
        if len(self.start_urls) == 1:
            yield Request(self._append_calendar_param(self.start_urls[0]), dont_filter=True)
        elif len(self.start_urls) == 0 and self.domain:
            yield Request(self._append_calendar_param(f"https://nomnom-prod-api.{self.domain}/restaurants/"))
        else:
            raise ValueError("Specify a 'domain' value or alternatively one URL in the 'start_urls' list attribute.")

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

    def parse(self, response: JsonResponse) -> Iterable[Feature]:
        if not isinstance(response, JsonResponse):
            self.logger.error(
                f"Unexpected response type {type(response)} (content-type {response.headers.get(b'Content-Type')})"
            )
            return
        for location in response.json()["restaurants"]:
            item = DictParser.parse(location)
            item["ref"] = location["extref"]
            if location.get("storename"):
                item["branch"] = location["name"].replace(location.get("storename"), "").strip()
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

    def post_process_item(self, item: Feature, response: JsonResponse, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
