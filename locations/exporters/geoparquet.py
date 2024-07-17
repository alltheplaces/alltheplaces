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

        self.features.append(item_to_geojson_feature(item))

    def finish_exporting(self):
        # Create a GeoDataFrame from the features
        gdf = geopandas.GeoDataFrame.from_features(self.features)

        # Write the GeoDataFrame to a Parquet file
        gdf.to_parquet(self.file)
