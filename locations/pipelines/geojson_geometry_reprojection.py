from pyproj import Transformer
from scrapy import Spider

from locations.items import Feature


class GeoJSONGeometryReprojectionPipeline:

    def process_item(self, item: Feature, spider: Spider):
        """
        If the `geometry` field of an item contains GeoJSON geometry with a
        coordinate reference system (CRS) projection other than EPSG:4326,
        attempt to convert to EPSG:4326.

        Currently only works for `Point` geometry.
        """
        if not item.get("geometry"):
            return item
        if item["geometry"].get("type") != "Point":
            return item
        if not item["geometry"].get("coordinates"):
            return item
        if not isinstance(item["geometry"]["coordinates"], list):
            return item
        if len(item["geometry"]["coordinates"]) != 2:
            return item
        if not item["geometry"].get("crs"):
            return item
        if item["geometry"]["crs"].get("type") != "name":
            return item
        if not item["geometry"]["crs"].get("properties"):
            return item
        if not item["geometry"]["crs"]["properties"].get("name"):
            return item
        if not item["geometry"]["crs"]["properties"]["name"].startswith("EPSG:"):
            return item
        original_projection = int(item["geometry"]["crs"]["properties"]["name"].removeprefix("EPSG:"))
        transformer = Transformer.from_crs(original_projection, 4326)
        new_geometry = {
            "type": "Point",
            "crs": {
                "type": "name",
                "properties": {
                    "name": "EPSG:4326"
                }
            },
            "coordinates": list(transformer.transform(item["geometry"]["coordinates"][1], item["geometry"]["coordinates"][0]))
        }
        item["geometry"] = new_geometry
        return item
