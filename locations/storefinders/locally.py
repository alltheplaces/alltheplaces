from typing import Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature

# To use this spider, specify one or more start_urls which have a domain of
# www.locally.com or brandname.locally.com and path of /stores/conversion_data
# Include all arguments in the URL.


class LocallySpider(Spider):
    """
    Locally provides an embeddable storefinder.
    https://support.locally.com/en/support/solutions/articles/14000098813-store-locator-overview

    To use, specify `start_urls`
    """

    allowed_domains = []
    start_urls = []
    api_key = None  # Later, will refactor to this
    custom_settings = {"ROBOTSTXT_OBEY": False}

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
