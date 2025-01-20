from scrapy import Spider

from locations.items import Feature


class GeoJSONMultiPointSimplificationPipeline:

    def process_item(self, item: Feature, spider: Spider):
        """
        If MultiPoint geometry only contains a single coordinate, the geometry
        can be changed from MultiPoint to Point. Point is simpler for ATP
        users and tools to work with and has broader support than MultiPoint.
        """
        if not item.get("geometry"):
            return item
        if not item["geometry"].get("type"):
            return item
        if item["geometry"]["type"] != "MultiPoint":
            return item
        if not item["geometry"].get("coordinates"):
            return item
        if not isinstance(item["geometry"]["coordinates"], list):
            return item
        if len(item["geometry"]["coordinates"]) != 1:
            return item
        new_geometry = {
            "type": "Point",
            "coordinates": item["geometry"]["coordinates"][0],
        }
        item["geometry"] = new_geometry
        return item
