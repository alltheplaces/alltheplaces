from typing import Iterable

from geopandas import read_file
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.items import Feature


class FlatGeobufSpider(Spider):
    """
    A FlatGeobufSpider is a lightweight spider for extracting features from a
    single FlatGeobuf response returned from a specified `start_urls[0]`.

    To use this spider, specify a URL with `start_urls`.
    """

    def parse(self, response: Response) -> Iterable[Feature]:
        feature_collection = read_file(response.body).to_geo_dict()
        for feature in feature_collection["features"]:
            feature.update(feature.pop("properties"))
            feature["geometry"]["coordinates"] = list(feature["geometry"]["coordinates"])
            self.pre_process_data(feature)
            item = DictParser.parse(feature)
            yield from self.post_process_item(item, response, feature)

    def pre_process_data(self, feature: dict) -> None:
        """Override with any pre-processing on the data, ie normalising key names for DictParser."""

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        """Override ith any post process on the item"""
        yield item
