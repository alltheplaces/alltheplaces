import logging
from argparse import ArgumentParser
from logging import getLogger
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

logger = getLogger(__name__)
logging.basicConfig(level=logging.INFO, filename="geojson_to_parquet.log", filemode="a", encoding="utf-8")


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
            con.execute("SET memory_limit='4GB'")
            con.execute("SET threads=2")

            con.execute(
                f"""
            COPY (
                SELECT 
                    id,
                    type,
                    dataset_attributes,
                    properties,
                    ST_GeomFromGeoJSON(geometry) AS geometry
                FROM read_ndjson(
                        '{input_files_pattern}',
                        columns={{
                            'type': 'VARCHAR' ,
                            'id': 'VARCHAR',
                            'dataset_attributes': 'MAP(VARCHAR, VARCHAR)', 
                            'properties' : 'MAP(VARCHAR, VARCHAR)',
                            'geometry': 'JSON',
                            }}
                        )
            ) TO '{str(output_file_path)}'
            (FORMAT PARQUET, COMPRESSION 'ZSTD', ROW_GROUP_SIZE 65536);
            """
            )

            # # Debug: log the schema and a sample row
            # res = con.execute(f'describe select * from read_parquet("{str(output_file_path)}")').fetchall()
            # logger.info(f"Parquet file schema: {res}")
            # res = con.execute(f'SELECT * FROM read_parquet("{str(output_file_path)}") LIMIT 1').fetchone()
            # logger.info(f"Sample row from Parquet file: {res}")

            # TODO: size of group should be 128MB-256MB for better performance
            # TODO: spatial ordering
            # TODO: bbox metadata

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

    ndgeojson_file_paths = list(input_directory.glob("*.ndgeojson"))
    if not ndgeojson_file_paths:
        raise FileNotFoundError(f"No NdGeoJSON files found in directory: {input_directory}")

    to_parquet(input_directory, output_file_path)


if __name__ == "__main__":
    main()
