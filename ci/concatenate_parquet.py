import argparse
import glob
import json

import pyarrow.parquet


def align_schema(row_group: pyarrow.Table, schema: pyarrow.Schema) -> pyarrow.Table:
    """
    Align the schema of a table to match the unified schema.

    Args:
        row_group: The table to align.
        schema: The unified schema to align to.

    Returns:
        A new table with a schema matching the unified schema.
    """
    aligned_columns = []
    for field in schema:
        if field.name in row_group.schema.names:
            aligned_columns.append(row_group.column(field.name))
        else:
            # Create a column of nulls if the field is missing in the table
            aligned_columns.append(pyarrow.array([None] * row_group.num_rows, type=field.type).cast(field.type))

    return pyarrow.Table.from_arrays(aligned_columns, schema=schema)


def main():
    parser = argparse.ArgumentParser(description="Concatenate multiple Parquet files into a single Parquet file.")
    parser.add_argument("files", type=str, nargs="+", help="Parquet files")
    parser.add_argument(
        "-o", "--output", type=argparse.FileType("wb"), nargs="?", help="the path to the output Parquet file"
    )

    args = parser.parse_args()

    parquet_filenames = []
    for pattern in args.files:
        parquet_filenames.extend(glob.glob(pattern))

    if not parquet_filenames:
        exit(1)

    if args.output is None:
        exit(1)

    # Unify the schema of all Parquet files and gather the geoparquet metadata
    geo_metadata = {}
    schemas = []
    for parquet_filename in parquet_filenames:
        parquet_file = pyarrow.parquet.ParquetFile(parquet_filename)
        schemas.append(parquet_file.schema_arrow)

        if geo_metadata_str := parquet_file.metadata.metadata.get(b"geo"):
            this_geo_metadata = json.loads(geo_metadata_str)

            if not geo_metadata:
                geo_metadata = this_geo_metadata

            # Expand the bounding box to include all the bounding boxes
            if bounding_box := this_geo_metadata.get("columns", {}).get("geometry", {}).get("bbox"):
                geo_metadata["columns"]["geometry"]["bbox"] = [
                    min(geo_metadata["columns"]["geometry"]["bbox"][0], bounding_box[0]),
                    min(geo_metadata["columns"]["geometry"]["bbox"][1], bounding_box[1]),
                    max(geo_metadata["columns"]["geometry"]["bbox"][2], bounding_box[2]),
                    max(geo_metadata["columns"]["geometry"]["bbox"][3], bounding_box[3]),
                ]

            # Union the geometry types
            if geometry_types := this_geo_metadata.get("columns", {}).get("geometry", {}).get("geometry_types"):
                for geometry_type in geometry_types:
                    if geometry_type not in geo_metadata["columns"]["geometry"]["geometry_types"]:
                        geo_metadata["columns"]["geometry"]["geometry_types"].append(geometry_type)

    unified_schema = pyarrow.unify_schemas(schemas, promote_options="permissive")

    unified_metadata = unified_schema.metadata
    unified_metadata[b"geo"] = json.dumps(geo_metadata)
    unified_schema = unified_schema.with_metadata(unified_metadata)

    # Concatenate the Parquet files, extending the bounding box in the geoparquet metadata if necessary
    with pyarrow.parquet.ParquetWriter(args.output, unified_schema) as writer:
        for parquet_filename in parquet_filenames:
            parquet_file = pyarrow.parquet.ParquetFile(parquet_filename)

            for i in range(parquet_file.num_row_groups):
                row_group = parquet_file.read_row_group(i)
                aligned_row_group = align_schema(row_group, unified_schema)
                writer.write(aligned_row_group)


if __name__ == "__main__":
    main()
