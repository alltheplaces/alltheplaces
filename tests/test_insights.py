import argparse
import json

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


def _export_feature_to_file(feature, path):
    with open(path, "wb") as f:
        exporter = GeoJsonExporter(f, encoding="utf-8")
        exporter.spider_name = feature["extras"]["@spider"]
        exporter.export_item(feature)
        exporter.finish_exporting()


def _get_record_by_code(data, code):
    matching = [r for r in data["data"] if r["code"] == code]
    return matching[0] if matching else None


def test_atp_nsi_osm(tmp_path):
    test_cases = [
        (_create_feature("1", "Mcdonalds", "mcdonalds", "US", "Q38076"), "mcdonalds.geojson"),
        (_create_feature("2", "Burger King", "burger_king", "US", "Q177054"), "burger_king.geojson"),
        # No wikidata
        (_create_feature("3", "Subway", "subway", "US"), "subway.geojson"),
        # No country, no wikidata
        (_create_feature("4", "KFC", "kfc_de"), "kfc_de.geojson"),
        # No country
        (_create_feature("5", "Pizza Hut", "pizza_hut_gb", brand_wikidata="Q191615"), "pizza_hut_gb.geojson"),
    ]

    for feature, filename in test_cases:
        _export_feature_to_file(feature, tmp_path / filename)

    outfile = tmp_path / "_insights.json"
    command = InsightsCommand()
    opts = argparse.Namespace(outfile=outfile, filter_spiders=[])
    command.analyze_atp_nsi_osm([tmp_path], opts)

    with open(outfile) as f:
        actual = json.load(f)

    mcdonalds = _get_record_by_code(actual, "Q38076")
    assert mcdonalds is not None
    assert mcdonalds["atp_count"] == 1
    assert mcdonalds["atp_country_count"] == 1
    assert mcdonalds["atp_supplier_count"] == 1
    assert mcdonalds["atp_splits"] == {"US": {"mcdonalds": 1}}

    burger_king = _get_record_by_code(actual, "Q177054")
    assert burger_king is not None
    assert burger_king["atp_count"] == 1
    assert burger_king["atp_country_count"] == 1
    assert burger_king["atp_supplier_count"] == 1
    assert burger_king["atp_splits"] == {"US": {"burger_king": 1}}
