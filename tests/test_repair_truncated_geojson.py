import json
from pathlib import Path

import pytest

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


def test_truncated_geojson_is_salvaged_when_ndgeojson_is_empty(tmp_path: Path):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"

    feature_a = json.dumps(
        {k: v for k, v in FEATURE_A.items() if k != "dataset_attributes"},
        separators=(",", ":"),
    )
    feature_b = json.dumps(
        {k: v for k, v in FEATURE_B.items() if k != "dataset_attributes"},
        separators=(",", ":"),
    )
    geojson_path.write_text(
        '{"type":"FeatureCollection","dataset_attributes":{"@spider":"example"},"features":[\n'
        + feature_a
        + ",\n"
        + feature_b
        + ',\n{"type":"Feature","id":"c","prop',
        encoding="utf-8",
    )
    ndgeojson_path.write_text("", encoding="utf-8")

    repair_spider_output(geojson_path, ndgeojson_path)

    data = json.loads(geojson_path.read_text())
    assert [f["id"] for f in data["features"]] == ["a", "b"]
    assert data["dataset_attributes"] == {"@spider": "example"}
    assert data["features"] == [
        {k: v for k, v in FEATURE_A.items() if k != "dataset_attributes"},
        {k: v for k, v in FEATURE_B.items() if k != "dataset_attributes"},
    ]
    ndfeatures = [json.loads(line) for line in ndgeojson_path.read_text().splitlines()]
    assert ndfeatures == [dict(feature, dataset_attributes=data["dataset_attributes"]) for feature in data["features"]]

    # Running repair again must leave both synchronized files untouched.
    geojson_before = geojson_path.read_bytes()
    ndgeojson_before = ndgeojson_path.read_bytes()
    repair_spider_output(geojson_path, ndgeojson_path)
    assert geojson_path.read_bytes() == geojson_before
    assert ndgeojson_path.read_bytes() == ndgeojson_before


def test_truncated_geojson_ending_in_comma_is_salvaged_when_ndgeojson_is_missing_lines(
    tmp_path: Path,
):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"

    feature_a = json.dumps(
        {k: v for k, v in FEATURE_A.items() if k != "dataset_attributes"},
        separators=(",", ":"),
    )
    geojson_path.write_text(
        '{"type":"FeatureCollection","dataset_attributes":{"@spider":"example"},"features":[\n' + feature_a + ",\n",
        encoding="utf-8",
    )
    ndgeojson_path.write_text('{"type":"Feature","id":"a"', encoding="utf-8")

    repair_spider_output(geojson_path, ndgeojson_path)

    assert [f["id"] for f in json.loads(geojson_path.read_text())["features"]] == ["a"]
    assert json.loads(ndgeojson_path.read_text()) == dict(FEATURE_A, dataset_attributes={"@spider": "example"})


@pytest.mark.parametrize("operation", ["open", "replace"])
def test_salvage_is_skipped_when_ndgeojson_cannot_be_synchronized(tmp_path: Path, monkeypatch, caplog, operation):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"
    _write_complete_geojson(geojson_path, [FEATURE_A])
    original = geojson_path.read_bytes().removesuffix(b"\n]}\n") + b",\n"
    geojson_path.write_bytes(original)
    ndgeojson_path.write_text("", encoding="utf-8")
    original_operation = getattr(Path, operation)

    def fail_ndgeojson_sync(path, *args, **kwargs):
        if path == ndgeojson_path.with_suffix(".ndgeojson.tmp"):
            raise OSError("Cannot synchronize ndgeojson")
        return original_operation(path, *args, **kwargs)

    monkeypatch.setattr(Path, operation, fail_ndgeojson_sync)
    repair_spider_output(geojson_path, ndgeojson_path)

    assert geojson_path.read_bytes() == original
    assert ndgeojson_path.read_bytes() == b""
    assert "Skipping salvage" in caplog.text
    assert not list(tmp_path.glob("*.tmp"))


def test_ndgeojson_is_restored_when_geojson_replacement_fails(tmp_path: Path, monkeypatch, caplog):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"
    _write_complete_geojson(geojson_path, [FEATURE_A])
    original = geojson_path.read_bytes().removesuffix(b"\n]}\n") + b",\n"
    geojson_path.write_bytes(original)
    ndgeojson_path.write_text("", encoding="utf-8")
    original_replace = Path.replace

    def fail_geojson_replace(path, target):
        if path == geojson_path.with_suffix(".geojson.tmp"):
            raise OSError("Cannot replace geojson")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_geojson_replace)
    repair_spider_output(geojson_path, ndgeojson_path)

    assert geojson_path.read_bytes() == original
    assert ndgeojson_path.read_bytes() == b""
    assert "Skipping salvage" in caplog.text
    assert not list(tmp_path.glob("*.tmp"))


def test_salvage_stops_at_undecodable_bytes(tmp_path: Path):
    geojson_path = tmp_path / "example.geojson"
    ndgeojson_path = tmp_path / "example.ndgeojson"

    feature_a = json.dumps({k: v for k, v in FEATURE_A.items() if k != "dataset_attributes"}, separators=(",", ":"))
    feature_b = json.dumps({k: v for k, v in FEATURE_B.items() if k != "dataset_attributes"}, separators=(",", ":"))
    geojson_path.write_bytes(
        b'{"type":"FeatureCollection","dataset_attributes":{"@spider":"example"},"features":[\n'
        + feature_a.encode()
        + b",\n"
        + feature_b.replace("2", "\udcff").encode("utf-8", errors="surrogateescape")
        + b",\n"
    )
    ndgeojson_path.write_text("", encoding="utf-8")

    repair_spider_output(geojson_path, ndgeojson_path)

    assert [f["id"] for f in json.loads(geojson_path.read_text())["features"]] == ["a"]
