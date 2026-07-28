import json
from pathlib import Path

from ci.repair_truncated_geojson import repair_directory, repair_spider_output

FEATURE_A = {
    "type": "Feature",
    "id": "a",
    "dataset_attributes": {
        "@spider": "example",
        "spider:collection_time": "2026-01-01T00:00:00",
    },
    "properties": {"ref": "1"},
    "geometry": {"type": "Point", "coordinates": [1, 2]},
}
FEATURE_B = {
    "type": "Feature",
    "id": "b",
    "dataset_attributes": {
        "@spider": "example",
        "spider:collection_time": "2026-01-01T00:00:00",
    },
    "properties": {"ref": "2"},
    "geometry": {"type": "Point", "coordinates": [3, 4]},
}


def _write_ndgeojson(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_complete_geojson(path: Path, features: list[dict]) -> None:
    body = ",\n".join(
        json.dumps(
            {k: v for k, v in f.items() if k != "dataset_attributes"},
            separators=(",", ":"),
        )
        for f in features
    )
    path.write_text(
        '{"type":"FeatureCollection","dataset_attributes":{"@spider":"example"},"features":[\n' + body + "\n]}\n",
        encoding="utf-8",
    )


def test_complete_files_are_left_untouched(tmp_path: Path):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"

    _write_complete_geojson(geojson_path, [FEATURE_A, FEATURE_B])
    _write_ndgeojson(ndgeojson_path, [json.dumps(FEATURE_A), json.dumps(FEATURE_B)])

    geojson_before = geojson_path.read_bytes()
    ndgeojson_before = ndgeojson_path.read_bytes()

    repair_spider_output(geojson_path, ndgeojson_path)

    assert geojson_path.read_bytes() == geojson_before
    assert ndgeojson_path.read_bytes() == ndgeojson_before


def test_empty_geojson_is_treated_as_valid_zero_item_output(tmp_path: Path):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"

    geojson_path.write_text("", encoding="utf-8")
    ndgeojson_path.write_text("", encoding="utf-8")

    repair_spider_output(geojson_path, ndgeojson_path)

    assert geojson_path.read_text() == ""


def test_missing_trailer_is_rebuilt_from_ndgeojson(tmp_path: Path):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"

    # Simulates a process killed right after the comma separator for the next
    # (never-written) item was flushed but before the "]}\n" trailer.
    geojson_path.write_text(
        '{"type":"FeatureCollection","dataset_attributes":{"@spider":"example"},"features":[\n'
        '{"type":"Feature","id":"a","properties":{"ref":"1"},"geometry":{"type":"Point","coordinates":[1,2]}},\n',
        encoding="utf-8",
    )
    _write_ndgeojson(ndgeojson_path, [json.dumps(FEATURE_A), json.dumps(FEATURE_B)])

    repair_spider_output(geojson_path, ndgeojson_path)

    rebuilt = json.loads(geojson_path.read_text())
    assert rebuilt["type"] == "FeatureCollection"
    assert rebuilt["dataset_attributes"] == FEATURE_A["dataset_attributes"]
    assert [f["id"] for f in rebuilt["features"]] == ["a", "b"]
    assert "dataset_attributes" not in rebuilt["features"][0]


def test_malformed_trailing_ndgeojson_line_is_dropped_and_geojson_rebuilt(
    tmp_path: Path,
):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"

    geojson_path.write_text(
        '{"type":"FeatureCollection","dataset_attributes":{},"features":[\n',
        encoding="utf-8",
    )
    _write_ndgeojson(
        ndgeojson_path,
        [
            json.dumps(FEATURE_A),
            '{"type":"Feature","id":"b","properties":{"ref":"2"},"geometry":{"type":"Poin',
        ],
    )

    repair_spider_output(geojson_path, ndgeojson_path)

    remaining_ndgeojson_lines = ndgeojson_path.read_text().strip().splitlines()
    assert len(remaining_ndgeojson_lines) == 1
    assert json.loads(remaining_ndgeojson_lines[0])["id"] == "a"

    rebuilt = json.loads(geojson_path.read_text())
    assert [f["id"] for f in rebuilt["features"]] == ["a"]


def test_no_usable_features_leaves_geojson_alone(tmp_path: Path, caplog):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"

    geojson_path.write_text(
        '{"type":"FeatureCollection","dataset_attributes":{},"features":[\n',
        encoding="utf-8",
    )
    ndgeojson_path.write_text('{"type":"Feature","id":"a","properties":{}, "geom', encoding="utf-8")

    original = geojson_path.read_bytes()
    repair_spider_output(geojson_path, ndgeojson_path)

    assert geojson_path.read_bytes() == original
    assert ndgeojson_path.read_text() == ""


def test_repair_directory_processes_every_spider(tmp_path: Path):
    _write_ndgeojson(tmp_path / "good.ndgeojson", [json.dumps(FEATURE_A)])
    _write_complete_geojson(tmp_path / "good.geojson", [FEATURE_A])

    (tmp_path / "broken.geojson").write_text(
        '{"type":"FeatureCollection","dataset_attributes":{},"features":[\n',
        encoding="utf-8",
    )
    _write_ndgeojson(tmp_path / "broken.ndgeojson", [json.dumps(FEATURE_A), json.dumps(FEATURE_B)])

    repair_directory(tmp_path)

    rebuilt = json.loads((tmp_path / "broken.geojson").read_text())
    assert [f["id"] for f in rebuilt["features"]] == ["a", "b"]
