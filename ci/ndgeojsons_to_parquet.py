import logging
from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple

import duckdb
import json
import pyarrow.parquet as pq
import pyarrow as pa

logger = getLogger(__name__)
logging.basicConfig(level=logging.INFO, filename="ndgeojson_to_parquet.log", filemode="a", encoding="utf-8")


def to_parquet(input_dir_path: Path, output_file_path: Path) -> None:
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    if output_file_path.exists():
        output_file_path.unlink()

    input_files_pattern = str(input_dir_path / "*.ndgeojson")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "temp.db"
        with duckdb.connect(db_path.as_posix()) as con:
            con.install_extension("spatial")
            con.load_extension("spatial")

            con.execute(f"SET temp_directory='{temp_dir}'")
            con.execute("SET memory_limit='1GB'")
            con.execute("SET threads=2")

            con.execute(f"""
            CREATE TABLE geojson_data AS
                SELECT
                    id,
                    type,
                    dataset_attributes,
                    properties,
                    ST_GeomFromGeoJSON(geometry) AS geom
                FROM read_ndjson(
                    '{input_files_pattern}',
                    columns={{
                        'type': 'VARCHAR' ,
                        'id': 'VARCHAR',
                        'dataset_attributes': 'MAP(VARCHAR, VARCHAR)',
                        'properties' : 'MAP(VARCHAR, VARCHAR)',
                        'geometry': 'JSON',
                        }}
                    );
            """)

            # compute overall bbox and geometry types from the created table
            bbox_res = con.execute(
                "SELECT min(ST_XMin(geom)), min(ST_YMin(geom)), max(ST_XMax(geom)), max(ST_YMax(geom)) FROM geojson_data"
            ).fetchone()

            geom_types_raw = con.execute("SELECT DISTINCT ST_GeometryType(geom) FROM geojson_data").fetchall()
            geom_types = [t[0] for t in geom_types_raw if t and t[0] is not None]

            # write parquet with a larger row group size (target 64-256 MB). 128MB chosen here.
            row_group_size = 134217728

            con.execute(f"""
            COPY (
                SELECT
                    id,
                    type,
                    dataset_attributes,
                    properties,
                    geom,
                    {{
                        'xmin': ST_XMin(geom),
                        'ymin': ST_YMin(geom),
                        'xmax': ST_XMax(geom),
                        'ymax': ST_YMax(geom)
                    }} as bbox
                FROM geojson_data
                ORDER BY ST_Hilbert(geom)
            ) TO '{str(output_file_path)}'
            (FORMAT PARQUET, COMPRESSION 'ZSTD', ROW_GROUP_SIZE {row_group_size});
            """)

            # Write GeoParquet metadata using pyarrow (pyarrow must be installed)
            table = pq.read_table(str(output_file_path))

            xmin, ymin, xmax, ymax = bbox_res
            geo_meta = {
                "version": "1.1.0",
                "primary_column": "geom",
                "columns": {
                    "geom": {"encoding": "WKB", "geometry_types": geom_types or ["Unknown"], "crs": "EPSG:4326"}
                },
                "bbox": [xmin, ymin, xmax, ymax],
            }

            existing_md = table.schema.metadata or {}
            new_md = dict(existing_md)
            new_md[b"geo"] = json.dumps(geo_meta, ensure_ascii=False).encode("utf-8")

            table = table.replace_schema_metadata(new_md)

            pq.write_table(table, str(output_file_path), compression="ZSTD")

    logger.info(f"✓ Created {output_file_path}")


def main() -> None:
    parser = ArgumentParser(description="Pack collection of NdGeoJSON files to Parquet format")
    parser.add_argument(
        "-d", "--directory", type=str, required=True, nargs="?", help="Directory containing NdGeoJSON files"
    )
    parser.add_argument("-o", "--output", type=str, required=True, nargs="?", help="Output Parquet file path")

    args = parser.parse_args()
    input_directory = Path(args.directory)
    output_file_path = Path(args.output)

    ndgeojson_file_paths = list(input_directory.glob("*.ndgeojson"))
    if not ndgeojson_file_paths:
        raise FileNotFoundError(f"No NdGeoJSON files found in directory: {input_directory}")

    to_parquet(input_directory, output_file_path)


if __name__ == "__main__":
    main()
