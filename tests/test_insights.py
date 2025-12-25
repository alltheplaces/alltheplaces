import argparse
import json
from pathlib import Path

from locations.commands.insights import InsightsCommand
from locations.exporters.geojson import GeoJsonExporter
from locations.items import Feature


def _create_feature(ref, name, spider, country=None, brand_wikidata=None, lat=0.0, lon=0.0):
    feature_data = {"ref": ref, "name": name, "lat": lat, "lon": lon, "extras": {"@spider": spider}}
    if country:
        feature_data["country"] = country
    if brand_wikidata:
        feature_data["brand_wikidata"] = brand_wikidata
    return Feature(feature_data)


def _export_features_to_file(features: list[Feature], path: str):
    with open(path, "wb") as f:
        exporter = GeoJsonExporter(f, encoding="utf-8")
        exporter.spider_name = features[0]["extras"]["@spider"]
        for feature in features:
            exporter.export_item(feature)
        exporter.finish_exporting()


def _generate_spider_file(spider_name: str, q_code: str, count: int, country: str, file_dir: Path) -> str:
    features = []
    for i in range(count):
        feature = _create_feature(
            ref=f"{spider_name}_{i}",
            name=f"Test Place {i}",
            spider=spider_name,
            country=country,
            brand_wikidata=q_code,
        )
        features.append(feature)
    file_path = f"{spider_name}.geojson"
    _export_features_to_file(features, file_dir / file_path)


def _get_record_by_code(data, code):
    matching = [r for r in data["data"] if r["code"] == code]
    return matching[0] if matching else None


def test_atp_nsi_osm(tmp_path):
    poi_count = 1000
    test_cases = [
        ("mcdonalds", "Q38076", poi_count, "US"),
        ("mcdonalds_fr", "Q38076", poi_count, "FR"),
        ("burger_king", "Q177054", poi_count, "US"),
        # No wikidata
        ("subway", None, poi_count, "US"),
        # No country, no wikidata
        ("kfc_de", None, poi_count, None),
        # No country
        ("pizza_hut_gb", "Q191615", poi_count, None),
    ]

    for case in test_cases:
        _generate_spider_file(*case, file_dir=tmp_path)

    outfile = tmp_path / "_insights.json"
    command = InsightsCommand()
    opts = argparse.Namespace(outfile=outfile, filter_spiders=[], workers=1)
    command.analyze_atp_nsi_osm([tmp_path], opts)

    with open(outfile) as f:
        actual = json.load(f)

    mcdonalds = _get_record_by_code(actual, "Q38076")
    assert mcdonalds is not None
    assert mcdonalds["atp_count"] == poi_count * 2
    assert mcdonalds["atp_country_count"] == 2
    assert mcdonalds["atp_supplier_count"] == 2
    assert mcdonalds["atp_splits"] == {"US": {"mcdonalds": poi_count}, "FR": {"mcdonalds_fr": poi_count}}

    burger_king = _get_record_by_code(actual, "Q177054")
    assert burger_king is not None
    assert burger_king["atp_count"] == poi_count
    assert burger_king["atp_country_count"] == 1
    assert burger_king["atp_supplier_count"] == 1
    assert burger_king["atp_splits"] == {"US": {"burger_king": poi_count}}


"""
Experiments:

### 1
Number of POIs: 1M per spider (5 spiders)
Number of processes: 1
Time taken: 12.085577964782715

### 2
Number of POIs: 1M per spider (5 spiders)
Number of processes: 5
Time taken: 5.676903009414673

"""
