import argparse
import gzip
import json
import shutil
from pathlib import Path

import pytest

from locations.commands.insights import InsightsCommand
from locations.exporters.geojson import GeoJsonExporter
from locations.exporters.ld_geojson import LineDelimitedGeoJsonExporter
from locations.items import Feature


def _make_features(spider: str, q_code: str, count: int, country: str) -> list[Feature]:
    return [
        Feature(ref=f"{spider}_{i}", country=country, brand_wikidata=q_code, extras={"@spider": spider})
        for i in range(count)
    ]


def _to_file(features: list[Feature], path: Path, format: str = "ndgeojson", compress: bool = False) -> None:
    exporter = (GeoJsonExporter if format == "geojson" else LineDelimitedGeoJsonExporter)(open(path, "wb"))
    if format == "geojson":
        exporter.spider_name = features[0]["extras"]["@spider"]
    for feature in features:
        exporter.export_item(feature)
    exporter.finish_exporting()

    if compress:
        with open(path, "rb") as f_in, gzip.open(f"{path}.gz", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        path.unlink()


def _analyze_atp_nsi_osm(tmp_path: Path) -> dict:
    outfile = tmp_path / "_insights.json"
    InsightsCommand().analyze_atp_nsi_osm([tmp_path], argparse.Namespace(outfile=outfile, filter_spiders=[], workers=1))
    return json.load(outfile.open())


@pytest.mark.parametrize(
    "compress,format",
    [
        (False, "geojson"),
        (True, "geojson"),
        (False, "ndgeojson"),
        (True, "ndgeojson"),
    ],
)
def test_format_and_compression(tmp_path, compress: bool, format: str):
    _to_file(_make_features("mcdonalds", "Q38076", 10, "US"), tmp_path / f"mcdonalds.{format}", format, compress)

    results = _analyze_atp_nsi_osm(tmp_path)
    brand = next(r for r in results["data"] if r["code"] == "Q38076")

    assert brand["atp_count"] == 10
    assert brand["atp_splits"] == {"US": {"mcdonalds": 10}}


def test_multiple_spiders_same_brand(tmp_path):
    _to_file(_make_features("mcdonalds", "Q38076", 10, "US"), tmp_path / "mcdonalds.ndgeojson")
    _to_file(_make_features("mcdonalds_fr", "Q38076", 10, "FR"), tmp_path / "mcdonalds_fr.ndgeojson")

    results = _analyze_atp_nsi_osm(tmp_path)
    brand = next(r for r in results["data"] if r["code"] == "Q38076")

    assert brand["atp_count"] == 20
    assert brand["atp_country_count"] == 2
    assert brand["atp_supplier_count"] == 2
    assert brand["atp_splits"] == {"US": {"mcdonalds": 10}, "FR": {"mcdonalds_fr": 10}}
    assert brand["osm_count"] > 0


def test_multiple_brands_same_spider(tmp_path):
    features = (
        _make_features("renault", "Q6686", 10, "FR")
        + _make_features("renault", "Q6686", 10, "TR")
        + _make_features("renault", "Q27460", 10, "TR")
    )
    _to_file(features, tmp_path / "renault.ndgeojson")

    results = _analyze_atp_nsi_osm(tmp_path)

    renault = next(r for r in results["data"] if r["code"] == "Q6686")
    assert renault["atp_count"] == 20
    assert renault["atp_country_count"] == 2
    assert renault["atp_supplier_count"] == 1
    assert renault["atp_splits"] == {"FR": {"renault": 10}, "TR": {"renault": 10}}
    assert renault["osm_count"] > 0

    dacia = next(r for r in results["data"] if r["code"] == "Q27460")
    assert dacia["atp_count"] == 10
    assert dacia["atp_country_count"] == 1
    assert dacia["atp_supplier_count"] == 1
    assert dacia["atp_splits"] == {"TR": {"renault": 10}}
    assert dacia["osm_count"] > 0


def test_missing_wikidata_and_country(tmp_path):
    _to_file(_make_features("mcdonalds", None, 10, "US"), tmp_path / "mcdonalds.geojson", "geojson")
    _to_file(_make_features("burger_king", None, 10, None), tmp_path / "burger_king.geojson", "geojson")

    results = _analyze_atp_nsi_osm(tmp_path)

    assert "data" in results
