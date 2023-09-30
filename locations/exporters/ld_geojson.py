import logging

from scrapy.exporters import JsonLinesItemExporter

from locations.exporters.geojson import compute_hash, get_dataset_attributes, item_to_properties


class LineDelimitedGeoJsonExporter(JsonLinesItemExporter):
    dataset_attributes = None
    first_item = True

    def export_item(self, item):
        if self.first_item:
            self.first_item = False
            self.dataset_attributes = get_dataset_attributes(item["extras"].get("@spider"))
        super().export_item(item)

    def _get_serialized_fields(self, item, default_value=None, include_empty=None):
        feature = []
        feature.append(("type", "Feature"))
        feature.append(("id", compute_hash(item)))
        feature.append(("dataset_attributes", self.dataset_attributes))
        feature.append(("properties", item_to_properties(item)))

        lat = item.get("lat")
        lon = item.get("lon")
        geometry = item.get("geometry")
        if lat and lon and not geometry:
            try:
                geometry = {
                    "type": "Point",
                    "coordinates": [float(item["lon"]), float(item["lat"])],
                }
            except ValueError:
                logging.warning("Couldn't convert lat (%s) and lon (%s) to float", lat, lon)
        feature.append(("geometry", geometry))

        return feature
