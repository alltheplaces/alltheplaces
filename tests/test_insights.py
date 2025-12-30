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


def _export_features(features: list[Feature], path: Path, compress: bool, format: str) -> None:
    exporter_class = GeoJsonExporter if format == "geojson" else LineDelimitedGeoJsonExporter

    with open(path, "wb") as f:
        exporter = exporter_class(f)
        if format == "geojson":
            exporter.spider_name = features[0]["extras"]["@spider"]
        for feature in features:
            exporter.export_item(feature)
        exporter.finish_exporting()

    if compress:
        with open(path, "rb") as f_in, gzip.open(f"{path}.gz", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)
        path.unlink()


def _generate_spider_file(
    spider: str, q_code: str, count: int, country: str, output_dir: Path, compress: bool, format: str
) -> None:
    features = [
        Feature(
            ref=f"{spider}_{i}",
            country=country,
            brand_wikidata=q_code,
            extras={"@spider": spider},
        )
        for i in range(count)
    ]
    _export_features(features, output_dir / f"{spider}.{format}", compress, format)


@pytest.mark.parametrize(
    "compress,format",
    [
        (False, "geojson"),
        (True, "geojson"),
        (False, "ndgeojson"),
        (True, "ndgeojson"),
    ],
)
def test_atp_nsi_osm_geojson(tmp_path, compress: bool, format: str):
    count = 1000

    test_spiders = [
        ("mcdonalds", "Q38076", count, "US"),
        ("mcdonalds_fr", "Q38076", count, "FR"),
        ("burger_king", "Q177054", count, "US"),
        ("subway", None, count, "US"),  # No wikidata
        ("kfc_de", None, count, None),  # No country, no wikidata
        ("pizza_hut_gb", "Q191615", count, None),  # No country
    ]

    for spider, q_code, cnt, country in test_spiders:
        _generate_spider_file(spider, q_code, cnt, country, tmp_path, compress, format)

    outfile = tmp_path / "_insights.json"
    command = InsightsCommand()
    command.analyze_atp_nsi_osm([tmp_path], argparse.Namespace(outfile=outfile, filter_spiders=[], workers=1))

    with open(outfile) as f:
        results = json.load(f)

    def get_record(code: str) -> dict:
        return next((r for r in results["data"] if r["code"] == code), None)

    mcdonalds = get_record("Q38076")
    assert mcdonalds is not None
    assert mcdonalds["atp_count"] == count * 2
    assert mcdonalds["atp_country_count"] == 2
    assert mcdonalds["atp_supplier_count"] == 2
    assert mcdonalds["atp_splits"] == {"US": {"mcdonalds": count}, "FR": {"mcdonalds_fr": count}}
    assert mcdonalds["osm_count"] > 0

    burger_king = get_record("Q177054")
    assert burger_king is not None
    assert burger_king["atp_count"] == count
    assert burger_king["atp_country_count"] == 1
    assert burger_king["atp_supplier_count"] == 1
    assert burger_king["atp_splits"] == {"US": {"burger_king": count}}
    assert burger_king["osm_count"] > 0
