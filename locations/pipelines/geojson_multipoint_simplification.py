from locations.geo import extract_geojson_point_geometry
from locations.items import Feature


class GeoJSONMultiPointSimplificationPipeline:

    def process_item(self, item: Feature):
        """
        If MultiPoint geometry only contains a single coordinate, the geometry
        can be changed from MultiPoint to Point. Point is simpler for ATP
        users and tools to work with and has broader support than MultiPoint.
        """
        if geometry := item.get("geometry"):
            if new_geometry := extract_geojson_point_geometry(geometry):
                item["geometry"] = new_geometry
        return item
