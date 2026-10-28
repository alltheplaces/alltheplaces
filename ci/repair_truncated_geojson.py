import json
import logging
import sys
from argparse import ArgumentParser
from pathlib import Path

logger = logging.getLogger(__name__)

# Written by GeoJsonExporter.finish_exporting() once a spider closes cleanly.
# Its absence means the spider process was killed (OOM, timeout, crash) before
# Scrapy's spider_closed signal ever fired.
GEOJSON_TRAILER = b"\n]}\n"


def _looks_complete(geojson_path: Path) -> bool:
    size = geojson_path.stat().st_size
    if size == 0:
        # A spider that scraped zero items never gets its header/trailer
        # written either (see GeoJsonExporter.export_item's first_item
        # check) - an empty file is the correct, valid output for that case.
        return True
    with geojson_path.open("rb") as f:
        f.seek(max(0, size - len(GEOJSON_TRAILER)))
        return f.read() == GEOJSON_TRAILER


def _split_ndgeojson_lines(ndgeojson_path: Path) -> tuple[list[str], list[dict], int]:
    """Read a newline-delimited GeoJSON file, separating lines that parse as
    valid JSON objects from malformed ones. Each line is written
    independently and carries its own "dataset_attributes", so a process
    killed mid-crawl can only ever leave a trailing line half-written -
    every earlier line is unaffected.
    """
    valid_lines = []
    valid_features = []
    dropped = 0
    with ndgeojson_path.open("r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            try:
                feature = json.loads(line)
            except json.JSONDecodeError:
                dropped += 1
                continue
            valid_lines.append(line)
            valid_features.append(feature)
    return valid_lines, valid_features, dropped


def _rebuild_geojson(geojson_path: Path, features: list[dict]) -> None:
    dataset_attributes = features[0].get("dataset_attributes", {})
    with geojson_path.open("w", encoding="utf-8") as out:
        out.write('{"type":"FeatureCollection","dataset_attributes":')
        json.dump(
            dataset_attributes,
            out,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        out.write(',"features":[\n')
        for i, feature in enumerate(features):
            if i:
                out.write(",\n")
            cleaned = {k: v for k, v in feature.items() if k != "dataset_attributes"}
            json.dump(cleaned, out, ensure_ascii=False, separators=(",", ":"))
        out.write("\n]}\n")


def _salvage_geojson_in_place(geojson_path: Path, ndgeojson_path: Path) -> int:
    """Close off a truncated GeoJSON file and synchronize its parquet input.

    GeoJsonExporter writes the header on one line and then one feature per
    line, so a killed process leaves complete feature lines followed by at
    most one partial line. Keep the header and every feature line that parses,
    then append the trailer. Copy each feature with the header's dataset
    attributes to ndgeojson before replacing the GeoJSON. Returns the number
    of features kept (0 means the files were left untouched).
    """
    with geojson_path.open("r", encoding="utf-8", errors="replace") as f:
        header = f.readline()
        if not header.rstrip("\n").endswith('"features":['):
            return 0
        try:
            dataset_attributes = json.loads(header + "]}").get("dataset_attributes", {})
        except json.JSONDecodeError:
            return 0
        if not isinstance(dataset_attributes, dict):
            return 0
        kept = []
        for raw_line in f:
            line = raw_line.strip().rstrip(",")
            if not line:
                continue
            try:
                feature = json.loads(line)
            except json.JSONDecodeError:
                break
            if not isinstance(feature, dict):
                break
            kept.append(line)
    if not kept:
        return 0

    tmp_path = geojson_path.with_suffix(geojson_path.suffix + ".tmp")
    nd_tmp_path = ndgeojson_path.with_suffix(ndgeojson_path.suffix + ".tmp")
    try:
        with nd_tmp_path.open("w", encoding="utf-8") as out:
            for line in kept:
                feature = json.loads(line)
                feature["dataset_attributes"] = dataset_attributes
                json.dump(feature, out, ensure_ascii=False, separators=(",", ":"))
                out.write("\n")
        with tmp_path.open("w", encoding="utf-8") as out:
            out.write(header)
            out.write(",\n".join(kept))
            out.write("\n]}\n")
        nd_tmp_path.replace(ndgeojson_path)
        tmp_path.replace(geojson_path)
    finally:
        nd_tmp_path.unlink(missing_ok=True)
        tmp_path.unlink(missing_ok=True)
    return len(kept)


def repair_spider_output(geojson_path: Path, ndgeojson_path: Path) -> None:
    geojson_complete = geojson_path.exists() and _looks_complete(geojson_path)

    valid_lines, valid_features, dropped = _split_ndgeojson_lines(ndgeojson_path)

    if dropped:
        with ndgeojson_path.open("w", encoding="utf-8") as f:
            for line in valid_lines:
                f.write(line + "\n")
        logger.info(
            "Dropped %d malformed trailing line(s) from %s",
            dropped,
            ndgeojson_path.name,
        )

    if geojson_complete:
        return

    if not valid_features:
        # The ndgeojson can be empty or lose its tail when the process is
        # SIGKILLed with buffered writes, so fall back to the geojson itself.
        try:
            salvaged = _salvage_geojson_in_place(geojson_path, ndgeojson_path) if geojson_path.exists() else 0
        except OSError as exc:
            logger.warning(
                "Skipping salvage of %s: could not synchronize repaired outputs with %s: %s",
                geojson_path.name,
                ndgeojson_path.name,
                exc,
            )
            return
        if salvaged:
            logger.info(
                "Closed truncated %s in place (%d feature(s)) and synchronized %s",
                geojson_path.name,
                salvaged,
                ndgeojson_path.name,
            )
        else:
            logger.warning(
                "%s is incomplete and neither it nor %s has usable features to rebuild from",
                geojson_path.name,
                ndgeojson_path.name,
            )
        return

    _rebuild_geojson(geojson_path, valid_features)
    logger.info(
        "Rebuilt %s from %s (%d feature(s))",
        geojson_path.name,
        ndgeojson_path.name,
        len(valid_features),
    )


def repair_directory(directory: Path) -> None:
    for ndgeojson_path in sorted(directory.glob("*.ndgeojson")):
        geojson_path = ndgeojson_path.with_suffix(".geojson")
        repair_spider_output(geojson_path, ndgeojson_path)


def main() -> None:
    parser = ArgumentParser(
        description="Repair .geojson/.ndgeojson output left incomplete by a spider process killed mid-crawl"
    )
    parser.add_argument(
        "-d",
        "--directory",
        required=True,
        help="Directory containing .geojson/.ndgeojson output files",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stderr)
    repair_directory(Path(args.directory))


if __name__ == "__main__":
    main()
