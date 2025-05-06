from scrapy import Spider

from locations.geo import convert_gj2008_to_rfc7946_point_geometry
from locations.items import Feature


class GeoJSONGeometryReprojectionPipeline:

    def process_item(self, item: Feature, spider: Spider):
        """
        If the `geometry` field of an item contains GeoJSON geometry with a
        coordinate reference system (CRS) projection other than EPSG:4326,
        attempt to convert to EPSG:4326.

        On failure to reproject, or if non-Point GeoJSON geometry exists, the
        supplied item is returned unmodified.

        Currently only works for `Point` geometry.
        """
        if new_geometry := convert_gj2008_to_rfc7946_point_geometry(item["geometry"]):
            item["geometry"] = new_geometry
        return item
