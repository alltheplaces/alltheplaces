import re
import time
from typing import AsyncIterator, Iterable
from urllib.parse import urljoin

from scrapy.http import Request, Response, TextResponse

from locations.items import Feature
from locations.storefinders.lib_cal import LibCalSpider

LOCATIONS_URL = "https://www.volusialibrary.org/hours-and-locations/"
# LibCal names carry the phone number, e.g. "DeBary Public Library (386) 668-3835".
NAME_REGEX = re.compile(r"^(?P<name>.+?)\s*(?P<phone>\(\d{3}\)\s*\d{3}-\d{4})?$")
CITY_REGEX = re.compile(r"^(?P<city>.+?)\s*,\s*(?P<state>[A-Z]{2})\s+(?P<postcode>\d{5})$")


class VolusiaCountyPublicLibraryUSSpider(LibCalSpider):
    name = "volusia_county_public_library_us"
    item_attributes = {"operator": "Volusia County Public Library", "operator_wikidata": "Q69471101"}
    libcal_host = "volusialibrary.libcal.com"
    libcal_iid = 6488

    async def start(self) -> AsyncIterator[Request]:
        # LibCal has names, phones and hours only, so addresses are read from
        # the library's single locations page first.
        yield Request(LOCATIONS_URL, callback=self.parse_locations_page)

    async def parse_locations_page(self, response: Response) -> AsyncIterator[Request]:
        # Cards are keyed without full stops, as the page has "John H
        # Dickerson" where LibCal has "John H. Dickerson".
        self.cards = {
            card.css("h3::text").get("").replace(".", "").strip().lower(): card
            for card in response.css("#inner-content .col.mt-3")
        }
        async for request in super().start():
            yield request

    def pre_process_data(self, location: dict, **kwargs) -> None:
        # Pierson's Thursday closes at "6am", a typo for 6pm, which would
        # otherwise be read as an overnight opening.
        for week in location.get("weeks") or []:
            for day in week.values():
                for hours in (day.get("times") or {}).get("hours") or []:
                    open_time = self.normalise_time(hours.get("from") or "")
                    close_time = self.normalise_time(hours.get("to") or "")
                    if (
                        open_time
                        and close_time
                        and close_time.endswith("am")
                        and not close_time.startswith("12")
                        and time.strptime(close_time, "%I:%M%p") < time.strptime(open_time, "%I:%M%p")
                    ):
                        hours["to"] = close_time.removesuffix("am") + "pm"

    def post_process_item(
        self, item: Feature, response: TextResponse, location: dict, **kwargs
    ) -> Iterable[Feature | Request]:
        m = NAME_REGEX.match(item["name"])
        item["name"], item["phone"] = m["name"], m["phone"]
        item["website"] = LOCATIONS_URL
        if (card := self.cards.get(item["name"].replace(".", "").lower())) is None:
            self.logger.warning("No card on the locations page for %s", item["name"])
            yield item
            return
        address = card.xpath("./p[1]")
        street = " ".join(address.xpath("./br/preceding-sibling::text()").getall())
        # e.g. "116 W. 1st Ave. , Building 6"
        item["street_address"] = re.sub(r"\s+,", ",", re.sub(r"\s+", " ", street)).strip()
        city = re.sub(r"\s+", " ", " ".join(address.xpath("./br/following-sibling::text()").getall())).strip()
        if city_match := CITY_REGEX.match(city):
            item["city"], item["state"], item["postcode"] = city_match.groups()
        if image := card.xpath("./following-sibling::div[1]//img/@src").get():
            item["image"] = urljoin(LOCATIONS_URL, image)
        # The directions links are Google Maps searches for the address or
        # the library's name, so there is no coordinate source.
        yield item
