import re
from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS, OpeningHours
from locations.items import Feature

CITY_STATE_POSTCODE_REGEX = re.compile(r"(.+?),+\s*(?:MI|Michigan)\s+(\d{5})")


class DetroitPublicLibraryUSSpider(Spider):
    name = "detroit_public_library_us"
    item_attributes = {"operator": "Detroit Public Library", "operator_wikidata": "Q5265986", "state": "MI"}
    start_urls = ["https://detroitpubliclibrary.org/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Request]:
        for card in response.css(".location-cards-iso .item"):
            url = card.css(".card-details a::attr(href)").get()
            if url.endswith("/mobile-library"):
                continue
            yield Request(
                url,
                callback=self.parse_location,
                cb_kwargs={
                    "address_lines": card.attrib["data-search-terms"].splitlines(),
                    "status": card.attrib["data-location-status"],
                },
            )

    def parse_location(self, response: Response, address_lines: list[str], status: str) -> Iterable[Feature]:
        item = Feature()
        item["ref"] = response.url.rstrip("/").rsplit("/", 1)[1]
        item["website"] = response.url

        label = response.css("h1::text").get().strip()
        if label == "Main":
            # The Main Library building is signed with the system name.
            item["branch"] = "Main Library"
            item["name"] = "Detroit Public Library"
        else:
            item["name"] = f"{label} Branch Library"
            item["branch"] = label

        item["street_address"] = address_lines[0].strip()
        if match := CITY_STATE_POSTCODE_REGEX.fullmatch(address_lines[1].strip()):
            item["city"], item["postcode"] = match.groups()

        if center := re.search(r"var center = \[\s*(-?[\d.]+),\s*(-?[\d.]+)\s*\]", response.text):
            item["lon"], item["lat"] = center.groups()

        # The page header carries the system's main number, so only read the
        # contact links in the location overview.
        overview = response.css('section[data-block-type="location-overview"]')
        item["phone"] = overview.css('nav a[href^="tel:"]::attr(href)').get("").removeprefix("tel:")
        item["email"] = overview.css('nav a[href^="mailto:"]::attr(href)').get("").removeprefix("mailto:")

        item["opening_hours"] = OpeningHours()
        if status == "temporarily-closed":
            item["opening_hours"].set_closed(DAYS)
        else:
            item["opening_hours"].add_ranges_from_string(
                " ".join(
                    f"{row.css('th::text').get()}: {''.join(row.css('td ::text').getall())}"
                    for row in overview.css("table tr")
                )
            )

        apply_category(Categories.LIBRARY, item)
        yield item
