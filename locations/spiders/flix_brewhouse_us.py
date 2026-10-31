import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser


class FlixBrewhouseUSSpider(Spider):
    """The locator states every theatre as linked data on the one page, so the pages
    it links are not requested: each one carries the same single MovieTheater, with
    nothing on it that the list does not already give.

    No brand is claimed in Wikidata: every "Flix Brewhouse" item there, and in the
    name suggestion index, is one individual theatre rather than the chain.
    """

    name = "flix_brewhouse_us"
    item_attributes = {"brand": "Flix Brewhouse"}
    start_urls = ["https://flixbrewhouse.com/theaters/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for theatre in self.theatres(response):
            item = LinkedDataParser.parse_ld(theatre)

            # The theatres are named by their town, or by the road they are on where a
            # town has two of them, and that is what identifies them locally.
            item["branch"] = item.pop("name", None)
            item["ref"] = (item.get("website") or "").rstrip("/").rsplit("/", 1)[-1] or None

            # One address begins with a stray building letter: "B, 3236 La Orilla Rd
            # NW #1", which already states its unit at the end.
            if street := item.get("street_address"):
                if trimmed := re.sub(r"^[A-Za-z],\s*", "", street):
                    if trimmed != street:
                        self.logger.warning(f"Dropped a leading building letter from {street!r}")
                    item["street_address"] = trimmed

            # The theatres brew their own beer and serve a full menu, but it is the
            # cinema that each one is, and the only other thing published about them
            # is a list of screen formats and promotions.
            apply_category(Categories.CINEMA, item)
            yield item

    def theatres(self, response: Response) -> Iterable[dict]:
        """Yield each MovieTheater from the list the locator publishes."""
        for blob in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(blob)
            except json.JSONDecodeError:
                self.logger.warning(f"Unparsed linked data on {response.url}")
                continue
            yield from self.walk(data)

    @staticmethod
    def walk(node: Any) -> Iterable[dict]:
        """Find the theatres, which the page nests inside an ItemList."""
        if isinstance(node, dict):
            if node.get("@type") == "MovieTheater":
                yield node
            for value in node.values():
                yield from FlixBrewhouseUSSpider.walk(value)
        elif isinstance(node, list):
            for value in node:
                yield from FlixBrewhouseUSSpider.walk(value)
