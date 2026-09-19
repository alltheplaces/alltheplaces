from datetime import date
from typing import Any, AsyncIterator, Iterable
from urllib.parse import quote

from scrapy import Spider
from scrapy.http import JsonRequest, Request, TextResponse

from locations.categories import Extras
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

API_URL = "https://api.communico.co/v1/{}"
IMAGE_URL = "https://static.libnet.info/images/locations/{}/{}"


class CommunicoSpider(Spider):
    """
    Communico Attend is an events, room booking and hours platform used by
    public library systems, mostly in the US. Its API lists a library
    system's locations and their hours.
    https://www.communico.co/

    To use, specify:
      - `communico_client`: the client name in the API path, e.g.
        "neworleans" for https://api.communico.co/v1/neworleans/locations.
        It is usually the subdomain of the library's *.libnet.info events
        site. An unknown client returns an empty list rather than an error.

    The hours endpoint returns one entry per date. Entries carrying a "day"
    are the regular weekly schedule and the rest are one-off exceptions,
    such as holidays and temporary closures, which are ignored. Half a year
    of dates is requested so that every weekday of the regular schedule is
    reached even for a location currently closed for several weeks; set
    `hours_days` to change that.

    Each client writes its own free-text address lines. Where the first line
    is not a street, it is taken to be the building the library is in and
    stored as `located_in`. Use `pre_process_data` and `post_process_item`
    for anything else a system needs, such as skipping locations which are
    not branches.
    """

    dataset_attributes: dict = {"source": "api", "api": "communico.co"}
    communico_client: str
    hours_days: int = 182

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="{}/opening-hours/{}/{}".format(
                API_URL.format(self.communico_client), date.today().isoformat(), self.hours_days
            ),
            callback=self.parse_hours,
        )

    def parse_hours(self, response: TextResponse, **kwargs: Any) -> Iterable[JsonRequest]:
        opening_hours = {location_id: self.parse_opening_hours(dates) for location_id, dates in response.json().items()}
        yield JsonRequest(
            url="{}/locations".format(API_URL.format(self.communico_client)),
            callback=self.parse,
            cb_kwargs={"opening_hours": opening_hours},
        )

    def parse(self, response: TextResponse, opening_hours: dict, **kwargs: Any) -> Iterable[Feature | Request]:
        for location in response.json():
            self.pre_process_data(location)
            item = self.parse_location(location, opening_hours)
            yield from self.post_process_item(item, response, location) or []

    def parse_location(self, location: dict, opening_hours: dict) -> Feature:
        item = DictParser.parse(location)
        item["name"] = " ".join(location["name"].split())
        item["city"] = location.get("locality")
        item["state"] = location.get("stateprovincecounty")
        item["postcode"] = location.get("ziporpostcode")

        address_lines = [location.get("line1") or "", location.get("line2") or "", location.get("line3") or ""]
        if address_lines[1] and not any(character.isdigit() for character in address_lines[0]):
            # A building rather than a street, e.g. "Allie Mae Williams
            # Multi-Service Center" followed by "2020 Jackson Avenue".
            item["located_in"] = address_lines.pop(0).strip()
        item["street_address"] = merge_address_lines(address_lines)

        item["phone"] = location.get("tel")
        if fax := location.get("fax"):
            item["extras"][Extras.FAX.value] = fax
        item["website"] = location.get("about_url")
        if image := location.get("image"):
            item["image"] = IMAGE_URL.format(self.communico_client, quote(image))
        item["opening_hours"] = opening_hours.get(location["id"])

        return item

    @staticmethod
    def parse_opening_hours(dates: dict) -> OpeningHours | None:
        oh = OpeningHours()
        for times in dates.values():
            if not (day := times.get("day")):
                # An exception to the weekly schedule, which carries the
                # date it applies to instead of a day of the week.
                continue
            if times["open"] == times["close"]:
                oh.set_closed(day)
            else:
                oh.add_range(day, times["open"], times["close"], time_format="%I:%M%p")
        return oh or None

    def pre_process_data(self, location: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: TextResponse, location: dict, **kwargs) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
