from scrapy import Spider

from locations.automatic_spider_generator import AutomaticSpiderGenerator, DetectionRequestRule
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class LocallySpider(Spider, AutomaticSpiderGenerator):
    """
    Locally provides an embeddable storefinder.
    https://support.locally.com/en/support/solutions/articles/14000098813-store-locator-overview

    To use, specify `start_urls`
    """

    custom_settings = {"ROBOTSTXT_OBEY": False}
    detection_rules = [
        DetectionRequestRule(
            url=r"^(?P<start_urls__list>https?:\/\/(?P<allowed_domains__list>[A-Za-z0-9\-.]+\.locally\.com)\/stores\/conversion_data\?.+)$"
        )
    ]

    def parse(self, response):
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

    def pre_process_data(self, location, **kwargs):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item, response, location):
        """Override with any post-processing on the item."""
        yield item
