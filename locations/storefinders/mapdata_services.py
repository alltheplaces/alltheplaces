from typing import Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.items import Feature


class MapDataServicesSpider(Spider):
    """
    API documentation available at:
    https://docs.mapdataservices.com.au/features/3.2.html

    To use this spider, specify an `api_brand_name` and `api_key` and
    optionally specify `api_filter` to filter out unwanted features.

    Override the `pre_process_data` and `post_process_item` functions to clean
    source data and to extract additional attributes with `DictParser` does
    not automatically extract.
    """

    dataset_attributes = {"source": "api", "api": "nowwhere.com.au"}
    custom_settings = {"ROBOTSTXT_OBEY": False}  # Invalid robots.txt causes parsing errors

    api_brand_name: str = ""
    api_key: str = ""
    api_filter: str | None = None

    def start_requests(self) -> Iterable[JsonRequest]:
        filter_clause = ""
        if self.api_filter:
            filter_clause = f"&filter={self.api_filter}"
        url = f"https://data.nowwhere.com.au/v3.2/features/{self.api_brand_name}/?=&key={self.api_key}&type=jsonp&BBox=-180 -90 180 90{filter_clause}"
        yield JsonRequest(url=url, headers={"Referer": "https://apps.nowwhere.com.au/"})

    def parse(self, response: Response) -> Iterable[Feature]:
        for feature in response.json()["Features"]:
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature)

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override with any post-processing on the item."""
        yield item
