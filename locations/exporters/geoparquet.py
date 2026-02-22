import geopandas
import pyarrow as pa
import pyarrow.parquet
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

        # Determine if we have a file path or a file-like object
        if isinstance(self.file, str):
            # It's a file path string, use gdf.to_parquet directly
            gdf.to_parquet(self.file)
        elif hasattr(self.file, "name") and isinstance(self.file.name, str):
            # It's a real file handle with a .name attribute (opened by Scrapy)
            # Use the file path instead of the file handle to avoid issues with geopandas.to_parquet()
            gdf.to_parquet(self.file.name)
        else:
            # It's a file-like object (BytesIO), convert geometry to WKB and use pyarrow directly
            gdf_wkb = gdf.to_wkb()
            table = pa.Table.from_pandas(gdf_wkb, preserve_index=False)
            pyarrow.parquet.write_table(table, self.file)
