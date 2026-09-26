import html
from typing import Any, AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Request, TextResponse

from locations.items import Feature


class TheEventsCalendarSpider(Spider):
    """
    The Events Calendar is a WordPress events plugin. Its REST API lists the
    venues events are held at.
    https://theeventscalendar.com/knowledgebase/introduction-to-the-events-calendar-rest-api/

    On most sites these are third-party venues hosting an event, but some
    operators, such as library systems, keep their own locations as venues
    and use the plugin as their location directory. Only use this store
    finder where that is the case.

    To use, specify `events_calendar_host`, e.g. "www.librarieshawaii.org".
    A site uses the plugin if https://<host>/wp-json/tribe/events/v1/venues
    returns a list of venues.

    Venues without a name or a street address, such as online or "to be
    decided" venues, are skipped, so `post_process_item` always gets an item
    with a name. Most sites also list venues which are not the operator's own
    locations, such as a park or restaurant hosting one event, or a room
    inside a location; skip these in `post_process_item`. The API has no
    opening hours.
    """

    dataset_attributes: dict = {"source": "api", "api": "theeventscalendar.com"}
    events_calendar_host: str
    page_size: int = 50

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url=f"https://{self.events_calendar_host}/wp-json/tribe/events/v1/venues?per_page={self.page_size}"
        )

    def parse(self, response: TextResponse, **kwargs: Any) -> Iterable[Feature | Request]:
        data = response.json()
        for venue in data["venues"]:
            self.pre_process_data(venue)
            if not self.clean(venue.get("venue")) or not self.clean(venue.get("address")):
                continue
            item = self.parse_venue(venue)
            yield from self.post_process_item(item, response, venue) or []
        if next_url := data.get("next_rest_url"):
            yield JsonRequest(url=next_url)

    @staticmethod
    def clean(value: Any) -> str | None:
        """Decode HTML entities, e.g. "Maui &#8211; Kahului", and collapse whitespace."""
        if not isinstance(value, str):
            return None
        return " ".join(html.unescape(value).split()) or None

    def parse_venue(self, venue: dict) -> Feature:
        item = Feature()
        item["ref"] = str(venue["id"])
        item["name"] = self.clean(venue.get("venue"))
        item["street_address"] = self.clean(venue.get("address"))
        item["city"] = self.clean(venue.get("city"))
        item["state"] = self.clean(venue.get("stateprovince") or venue.get("state") or venue.get("province"))
        item["postcode"] = self.clean(venue.get("zip"))
        item["country"] = self.clean(venue.get("country"))
        item["phone"] = self.clean(venue.get("phone"))
        # The venue's own page on the site, unless a full link to another page
        # is given; some sites enter a bare domain name instead.
        website = self.clean(venue.get("website")) or ""
        item["website"] = website if website.startswith(("https://", "http://")) else venue.get("url")
        item["lat"] = venue.get("geo_lat")
        item["lon"] = venue.get("geo_lng")
        if isinstance(image := venue.get("image"), dict):
            item["image"] = image.get("url")
        return item

    def pre_process_data(self, venue: dict, **kwargs) -> None:
        """Override with any pre-processing on the venue."""

    def post_process_item(self, item: Feature, response: TextResponse, venue: dict, **kwargs) -> Iterable[Feature]:
        """Override with any post-processing on the item, such as skipping venues which are not locations."""
        yield item
