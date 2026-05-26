import json
import logging
import sys
import traceback
from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
import pyarrow.parquet as pq

logger = getLogger(__name__)
# Log to both file and stderr so errors appear in ECS logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ndgeojson_to_parquet.log", mode="a", encoding="utf-8"),
        logging.StreamHandler(sys.stderr),
    ],
)


def to_parquet(input_dir_path: Path, output_file_path: Path) -> None:
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    if output_file_path.exists():
        output_file_path.unlink()

    input_files_pattern = str(input_dir_path / "*.ndgeojson")
    logger.info(f"Processing ndgeojson files matching: {input_files_pattern}")

    with TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "temp.db"
        logger.info(f"Using DuckDB version: {duckdb.__version__}")
        logger.info(f"Creating temporary database at: {db_path}")
        with duckdb.connect(db_path.as_posix()) as con:
            logger.info("Installing spatial extension...")
            con.install_extension("spatial")
            con.load_extension("spatial")
            logger.info("Spatial extension loaded successfully")

            logger.info("Configuring DuckDB settings...")
            con.execute(f"SET temp_directory='{temp_dir}'")
            con.execute("SET memory_limit='8GB'")
            con.execute("SET threads=2")
            con.execute("SET preserve_insertion_order=false")

            logger.info("Creating geojson_data table from ndgeojson files...")
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
            logger.info("Table created successfully")

            # compute overall bbox and geometry types from the created table
            logger.info("Computing bounding box...")
            bbox_res = con.execute(
                "SELECT min(ST_XMin(geom)), min(ST_YMin(geom)), max(ST_XMax(geom)), max(ST_YMax(geom)) FROM geojson_data"
            ).fetchone()
            logger.info(f"Bounding box: {bbox_res}")

            logger.info("Computing geometry types...")
            geom_types_raw = con.execute("SELECT DISTINCT ST_GeometryType(geom) FROM geojson_data").fetchall()
            geom_types = [t[0] for t in geom_types_raw if t and t[0] is not None]
            logger.info(f"Found geometry types: {geom_types}")

            # write parquet with a larger row group size (target 64-256 MB). 128MB chosen here.
            row_group_size = 134217728

            logger.info(f"Writing parquet file with row group size {row_group_size}...")
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
            logger.info("Parquet file written successfully")

            logger.info("Adding GeoParquet metadata...")
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

            logger.info("Writing final parquet file with metadata...")
            pq.write_table(table, str(output_file_path), compression="ZSTD")

    file_size = output_file_path.stat().st_size
    logger.info(f"✓ Created {output_file_path} ({file_size:,} bytes)")


def main() -> None:
    parser = ArgumentParser(description="Pack collection of NdGeoJSON files to Parquet format")
    parser.add_argument(
        "-d", "--directory", type=str, required=True, nargs="?", help="Directory containing NdGeoJSON files"
    )
    parser.add_argument("-o", "--output", type=str, required=True, nargs="?", help="Output Parquet file path")

    args = parser.parse_args()
    input_directory = Path(args.directory)
    output_file_path = Path(args.output)

    try:
        ndgeojson_file_paths = list(input_directory.glob("*.ndgeojson"))
        if not ndgeojson_file_paths:
            raise FileNotFoundError(f"No NdGeoJSON files found in directory: {input_directory}")

        logger.info(f"Found {len(ndgeojson_file_paths)} ndgeojson files to process")
        to_parquet(input_directory, output_file_path)
    except Exception as e:
        logger.error(f"Failed to create parquet file: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
