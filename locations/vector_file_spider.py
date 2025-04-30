from typing import Iterable

from geopandas import read_file
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.items import Feature


class VectorFileSpider(Spider):
    """
    A VectorFileSpider is a lightweight spider for extracting features from a
    vector file format response returned from a specified `start_urls[0]`.

    A wide variety of vector file formats are supported including:
    1. ESRI Shapefile
    2. GeoPackage
    3. FlatGeobuf
    4. GeoJSON (don't use with this spider, use JSONBlobSpider instead)

    Archived versions of the above listed vector file formats are also
    supported. For example, a ZIP archive of an ESRI Shapefile and associated
    files (.shp, .dbf, .shx).

    The details of file format support is available via the following
    documentation for the underlying Python and system libraries this spider
    type depends upon:
    1. https://geopandas.org/en/stable/docs/reference/api/geopandas.read_file.html
    2. https://pyogrio.readthedocs.io/en/latest/supported_formats.html
    3. https://gdal.org/en/stable/drivers/vector/index.html

    To use this spider, specify a URL with `start_urls`.

    Override `pre_process_data` and/or `post_process_item` methods to modify
    the fields of data extracted from the source vector file. These overriden
    methods can be used extract additional non-standard fields which
    DictParser doesn't automatically extract, or to clean up fields of data
    that are incorrect or formatted incorrectly.
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
