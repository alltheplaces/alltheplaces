import geopandas
from scrapy.exporters import BaseItemExporter

from locations.exporters.geojson import item_to_geojson_feature


class GeoparquetExporter(BaseItemExporter):
    def __init__(self, file, **kwargs):
        super().__init__(**kwargs)
        self.first_item = True
        self.file = file
        self.features = []

    def export_item(self, item):
        if self.first_item:
            # TODO Figure out a way to attach dataset attributes to the parquet file.
            # self.write_dataset_attributes_table(item)
            self.first_item = False

        # Convert the item to a GeoJSON feature
        feature = item_to_geojson_feature(item)

        # Convert all attributes to strings so that the Parquet output is of consistent type.
        # Without this, the "global" Parquet file would have mixed types in the same column.
        for key, value in feature["properties"].items():
            feature["properties"][key] = str(value)

        self.features.append(feature)

    def finish_exporting(self):
        # Don't write an empty Parquet file
        if not self.features:
            return

        # Create a GeoDataFrame from the features
        gdf = geopandas.GeoDataFrame.from_features(self.features)

        # Write the GeoDataFrame to a Parquet file
        gdf.to_parquet(self.file)
