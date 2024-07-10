import argparse
import glob
import multiprocessing
import os.path

import geopandas
import pandas
import pyarrow
import pyogrio.errors


def read_file(filename):
    parquet_filename = filename.replace(".geojson", ".parquet")
    if os.path.exists(parquet_filename):
        return parquet_filename

    # Sometimes a single spider's scrape fails and the output file ends up
    # as an invalid GeoJSON feature collection.
    with open(filename, "r") as f:
        contents = f.read()
        # If the file ends with a comma and a newline, we need to remove the last comma and add the closing brackets
        if contents[-2:] == ",\n":
            with open(filename, "a") as f:
                f.seek(f.tell() - 2)
                f.write("\n]}")
        # If the file doesn't end with the closing brackets, we need to add them
        elif contents[-3:] != "]}\n":
            with open(filename, "a") as f:
                f.write("]}\n")

    try:
        df = geopandas.read_file(filename)
    except pyogrio.errors.DataSourceError as e:
        print(f"Error reading {filename}: {e}")
        return None

    # Convert all non-geometry columns to object type to avoid issues with mixed types in the concatenated output
    # parquet file
    for col in df.columns:
        if col != "geometry" and df[col].dtype != "object":
            df[col] = df[col].astype(str)

    try:
        df.to_parquet(parquet_filename)
        return parquet_filename
    except pyarrow.lib.ArrowException as e:
        print(f"Error writing {parquet_filename}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Process GeoJSON files into a GeoParquet file.")
    parser.add_argument("files", type=str, nargs="+", help="a path to a GeoJSON file")
    parser.add_argument(
        "-o", "--output", type=argparse.FileType("wb"), nargs="?", help="a path to the output GeoParquet file"
    )

    args = parser.parse_args()

    files = []
    for pattern in args.files:
        for file in glob.glob(pattern):
            if os.path.getsize(file) > 0:
                files.append(file)

    with multiprocessing.Pool(processes=32) as pool:
        parquet_filenames = pool.map(read_file, files)

    dataframes = []
    for f in parquet_filenames:
        if f is not None:
            df = pandas.read_parquet(f)
            dataframes.append(df)

    master_df = pandas.concat(dataframes)

    master_df.to_parquet(args.output)


if __name__ == "__main__":
    main()
