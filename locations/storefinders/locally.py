from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import Request, TextResponse

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class LocallySpider(Spider):
    """
    Locally provides an embeddable storefinder. For more information refer to:
    https://support.locally.com/en/support/solutions/articles/14000098813-store-locator-overview

    To use, specify a URL in `start_urls` which should generally have a domain
    of either www.locally.com or examplebrandname.locally.com, and with a path
    of "/stores/conversion_data". Include all query parameters in the URL.
    """

    start_urls: list[str] = []
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        if len(self.start_urls) != 1:
            raise ValueError("Specify one URL in the start_urls list attribute.")
        yield Request(url=self.start_urls[0])

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json()["markers"]:
            self.pre_process_data(location)
            item = DictParser.parse(location)
            item["opening_hours"] = OpeningHours()
            for day in DAYS_FULL:
                open = f"{day[:3].lower()}_time_open"
                close = f"{day[:3].lower()}_time_close"
                if not location.get(open) or len(str(location.get(open))) < 3:
                    continue
                item["opening_hours"].add_range(
                    day=day,
                    open_time=f"{str(location.get(open))[:-2]}:{str(location.get(open))[-2:]}",
                    close_time=f"{str(location.get(close))[:-2]}:{str(location.get(close))[-2:]}",
                )

            yield from self.post_process_item(item, response, location) or []

    def pre_process_data(self, location: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
