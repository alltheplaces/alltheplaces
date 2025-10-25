import logging
from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb
from duckdb import InvalidInputException

logger = getLogger(__name__)
logging.basicConfig(level=logging.WARNING, filename="geojson_to_parquet.log", filemode="a", encoding="utf-8")


def to_parquet(input_dir_path: Path, output_file_path: Path) -> None:
    """
    Convert large GeoJSON files to Parquet via intermediate conversions.
    Each GeoJSON is converted to Parquet first, then combined.
    """
    geojson_files = list(input_dir_path.glob("*.geojson"))
    if not geojson_files:
        raise FileNotFoundError(f"No .geojson files found in: {input_dir_path}")

    logger.info(f"Found {len(geojson_files)} GeoJSON files")

    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    if output_file_path.exists():
        output_file_path.unlink()

    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        temp_parquets = []

        with duckdb.connect("temp.db") as con:
            con.install_extension("spatial")
            con.load_extension("spatial")

            # Convert each GeoJSON to Parquet individually
            for i, geojson_file in enumerate(geojson_files, start=1):
                if geojson_file.stat().st_size == 0:
                    logger.warning(f"Skipping empty file: {geojson_file.name}")
                    continue

                logger.info(f"Converting {i}/{len(geojson_files)}: {geojson_file.name}")

                temp_parquet = temp_path / f"{geojson_file.stem}.parquet"
                temp_parquets.append(str(temp_parquet))
                try:
                    # Convert single GeoJSON to Parquet
                    con.execute(
                        f"""
                        COPY (
                            SELECT 
                                feature.id as id,
                                dataset_attributes,
                                feature.properties as properties,
                                feature.geometry as geometry
                            FROM (
                                SELECT 
                                    dataset_attributes,
                                    unnest(features, recursive := false) as feature
                                FROM read_json_auto(
                                '{str(geojson_file)}', 
                                maximum_object_size=1073741824
                                )
                            )
                        ) TO '{str(temp_parquet)}'
                        (FORMAT PARQUET, COMPRESSION 'ZSTD', ROW_GROUP_SIZE 100000);
                    """
                    )
                except InvalidInputException as e:
                    logger.error(f"Error converting {geojson_file.name}: {e}")
                    temp_parquets.pop()  # Remove failed file
                    continue

                # read back to verify
                # _ = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{str(temp_parquet)}')").fetchall()
                # print(f"{_}")
                # raise RuntimeError(f"Verification failed for {temp_parquet}")

            logger.info(f"Combining {len(temp_parquets)} parquet files...")

            # Combine all parquets into final output
            parquet_list = ", ".join(f"'{p}'" for p in temp_parquets)
            con.execute(
                f"""
                COPY (
                    SELECT * FROM read_parquet([{parquet_list}])
                ) TO '{str(output_file_path)}'
                (FORMAT PARQUET, COMPRESSION 'ZSTD', ROW_GROUP_SIZE 100000);
            """
            )

    logger.info(f"✓ Created {output_file_path}")


def main() -> None:
    parser = ArgumentParser(description="Pack collection of GeoJSON files to Parquet format.")
    parser.add_argument(
        "-d", "--directory", type=str, required=True, nargs="?", help="Directory containing GeoJSON files"
    )
    parser.add_argument("-o", "--output", type=str, required=True, nargs="?", help="Output Parquet file path")

    args = parser.parse_args()
    input_directory = Path(args.directory)
    output_file_path = Path(args.output)

    geojson_file_paths = list(input_directory.glob("*.ndgeojson"))
    if not geojson_file_paths:
        raise FileNotFoundError(f"No GeoJSON files found in directory: {input_directory}")

    to_parquet(input_directory, output_file_path)


if __name__ == "__main__":
    main()
