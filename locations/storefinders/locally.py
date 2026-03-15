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

    Presence of this storefinder is usually observed from requests made to:
      https://*.locally.com/stores/conversion_data?...

    To use this spider, specify:
      `company_id`: mandatory parameter, an integer value of the brand/company
                    found inside requests made on a storefinder page to
                    /stores/conversion_data?company_id=...
      `categories`: mandatory parameter, one or more categories of features to
                    return for the brand, such as ["Boutique", "Clearance"]
    """

    company_id: int
    categories: list[str] = []
    custom_settings = {"ROBOTSTXT_OBEY": False}

    async def start(self) -> AsyncIterator[Request]:
        company_id_str = str(self.company_id)
        for category in self.categories:
            url = f"https://www.locally.com/stores/conversion_data?has_data=true&company_id={company_id_str}&map_center_lat=0&map_center_lng=0&map_distance_diag=10000000&zoom_level=1&map_ne_lat=90&map_ne_lng=180&map_sw_lat=-90&map_sw_lng=-180&lang=en-int&category={category}"
            yield Request(url)

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json()["markers"]:
            self.pre_process_data(location)
            item = DictParser.parse(location)
            try:
                item["opening_hours"] = self.parse_opening_hours(location)
            except Exception as e:
                self.logger.warning("Error parsing opening hours for {} {}".format(item.get("ref"), e))

            yield from self.post_process_item(item, response, location) or []

    def parse_opening_hours(self, location: dict, **kwargs) -> OpeningHours:
        oh = OpeningHours()
        for day in DAYS_FULL:
            open = f"{day[:3].lower()}_time_open"
            close = f"{day[:3].lower()}_time_close"
            if not location.get(open) or len(str(location.get(open))) < 3:
                continue
            oh.add_range(
                day=day,
                open_time=f"{str(location.get(open))[:-2]}:{str(location.get(open))[-2:]}",
                close_time=f"{str(location.get(close))[:-2]}:{str(location.get(close))[-2:]}",
            )
        return oh

    def pre_process_data(self, location: dict, **kwargs) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
