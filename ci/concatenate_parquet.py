import argparse
import glob
import os.path

import geopandas
import pandas


def main():
    parser = argparse.ArgumentParser(description="Concatenate multiple Parquet files into a single Parquet file.")
    parser.add_argument("files", type=str, nargs="+", help="Parquet files")
    parser.add_argument(
        "-o", "--output", type=argparse.FileType("wb"), nargs="?", help="the path to the output Parquet file"
    )

    args = parser.parse_args()

    files = []
    for pattern in args.files:
        for file in glob.glob(pattern):
            if os.path.getsize(file) > 0:
                files.append(file)

    dataframes = []
    for f in files:
        if f is None:
            continue

        dataframes.append(geopandas.read_parquet(f))

    joined_df = geopandas.GeoDataFrame(pandas.concat(dataframes, ignore_index=True), crs=dataframes[0].crs)

    joined_df.to_parquet(args.output)


if __name__ == "__main__":
    main()
