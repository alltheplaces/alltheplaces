import json
import logging
import math
import sys
import traceback
from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
import psutil
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


def duckdb_memory_limit() -> str:
    total_bytes = psutil.virtual_memory().total
    # Reserve 2 GB for Python, pyarrow, and OS overhead
    reserved_bytes = 2 * 1024**3
    duckdb_bytes = max(total_bytes - reserved_bytes, reserved_bytes)
    duckdb_gb = math.floor(duckdb_bytes / 1024**3)
    return f"{duckdb_gb}GB"


# ST_Hilbert() returns a UINTEGER (32-bit) curve position. Used to split the
# table into spatially-contiguous batches so no single ORDER BY has to sort/
# materialize the whole dataset at once.
HILBERT_RANGE = 2**32

# Sorting and writing the whole table in one COPY holds the full row set
# (geometry + properties + dataset_attributes) in memory during the sort. On
# a ~43M row dataset that has been observed to exceed the container's memory
# limit and get silently OOM-killed (see #14341/#16158). Splitting into
# batches of roughly this many rows keeps each sort's peak memory bounded
# regardless of total dataset size.
TARGET_ROWS_PER_BATCH = 2_000_000


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
            memory_limit = duckdb_memory_limit()
            logger.info(
                f"Setting DuckDB memory limit to {memory_limit} (total system RAM: {psutil.virtual_memory().total / 1024**3:.1f} GB)"
            )
            con.execute(f"SET temp_directory='{temp_dir}'")
            con.execute(f"SET memory_limit='{memory_limit}'")
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

            row_count = con.execute("SELECT count(*) FROM geojson_data").fetchone()[0]
            num_batches = max(1, math.ceil(row_count / TARGET_ROWS_PER_BATCH))
            logger.info(f"Table has {row_count:,} rows; writing in {num_batches} spatial batch(es)")

            if num_batches > 1:
                # Bucket rows into spatially-contiguous ranges of the Hilbert curve so each
                # batch can be sorted and written independently, without needing the whole
                # table's rows in memory at once. Buckets won't be perfectly balanced (data
                # is denser in some regions than others), but this bounds the *typical* peak
                # memory of any single sort to a small fraction of the full dataset.
                con.execute("ALTER TABLE geojson_data ADD COLUMN batch_id INTEGER")
                con.execute(f"""
                    UPDATE geojson_data
                    SET batch_id = LEAST(
                        CAST(FLOOR(ST_Hilbert(geom) / ({HILBERT_RANGE} / {num_batches})) AS INTEGER),
                        {num_batches - 1}
                    )
                """)

            # write parquet with a larger row group size (target 64-256 MB). 128MB chosen here.
            row_group_size = 134217728

            batch_paths = []
            for batch_num in range(num_batches):
                batch_path = Path(temp_dir) / f"batch_{batch_num}.parquet"
                where_clause = f"WHERE batch_id = {batch_num}" if num_batches > 1 else ""
                logger.info(f"Writing batch {batch_num + 1}/{num_batches} to {batch_path}...")
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
                    {where_clause}
                    ORDER BY ST_Hilbert(geom)
                ) TO '{str(batch_path)}'
                (FORMAT PARQUET, COMPRESSION 'ZSTD', ROW_GROUP_SIZE {row_group_size});
                """)
                batch_paths.append(batch_path)
            logger.info("All batches written successfully")

        # DuckDB connection is now closed, releasing its memory before pyarrow runs.
        # Merge the batch files into the final output one row group at a time so we
        # never need to hold the full dataset in memory (unlike a read_table/write_table
        # round trip over the whole file, which was itself a prior OOM risk).
        logger.info("Merging batches into final parquet file with GeoParquet metadata...")

        if bbox_res is None:
            xmin, ymin, xmax, ymax = None, None, None, None
        else:
            xmin, ymin, xmax, ymax = bbox_res
        geo_meta = {
            "version": "1.1.0",
            "primary_column": "geom",
            # No "crs" key: per the GeoParquet spec, omitting it means the default of
            # OGC:CRS84 (WGS84, lon/lat axis order), which matches our WKB geometries.
            # "EPSG:4326" would be wrong here - that CRS formally specifies lat/lon axis
            # order, the opposite of what's actually stored, which readers (e.g. DuckDB)
            # correctly reject.
            "columns": {"geom": {"encoding": "WKB", "geometry_types": geom_types or ["Unknown"]}},
            "bbox": [xmin, ymin, xmax, ymax],
        }

        writer = None
        try:
            for batch_path in batch_paths:
                parquet_file = pq.ParquetFile(str(batch_path))
                for row_group_idx in range(parquet_file.num_row_groups):
                    row_group_table = parquet_file.read_row_group(row_group_idx)
                    if writer is None:
                        schema = row_group_table.schema.with_metadata(
                            {
                                **(row_group_table.schema.metadata or {}),
                                b"geo": json.dumps(geo_meta, ensure_ascii=False).encode("utf-8"),
                            }
                        )
                        writer = pq.ParquetWriter(str(output_file_path), schema, compression="ZSTD")
                    writer.write_table(row_group_table)

            if writer is None:
                # No rows in any batch (empty dataset) - still emit a valid, empty parquet
                # file with the right schema and GeoParquet metadata rather than nothing.
                schema = pq.ParquetFile(str(batch_paths[0])).schema_arrow.with_metadata(
                    {b"geo": json.dumps(geo_meta, ensure_ascii=False).encode("utf-8")}
                )
                writer = pq.ParquetWriter(str(output_file_path), schema, compression="ZSTD")
        finally:
            if writer is not None:
                writer.close()

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
