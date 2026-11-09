import json
import shutil
from pathlib import Path

import psutil
from pandas import read_parquet

from ci.ndgeojsons_to_parquet import cgroup_memory_limit_bytes, duckdb_memory_limit, to_parquet
from ci.repair_truncated_geojson import repair_directory


def _patch_cgroup_v2_path(monkeypatch, cgroup_v2_file: Path):
    monkeypatch.setattr(
        "ci.ndgeojsons_to_parquet.Path",
        lambda p: cgroup_v2_file if p == "/sys/fs/cgroup/memory.max" else Path(p),
    )


def test_cgroup_memory_limit_bytes_prefers_cgroup_v2(monkeypatch, tmp_path: Path):
    # Well below actual host RAM so it isn't mistaken for an unset/sentinel limit.
    limit_bytes = 1024**3  # 1 GiB
    cgroup_v2 = tmp_path / "memory.max"
    cgroup_v2.write_text(str(limit_bytes))
    _patch_cgroup_v2_path(monkeypatch, cgroup_v2)

    assert cgroup_memory_limit_bytes() == limit_bytes


def test_cgroup_memory_limit_bytes_ignores_unset_v2_limit(monkeypatch, tmp_path: Path):
    cgroup_v2 = tmp_path / "memory.max"
    cgroup_v2.write_text("max")
    _patch_cgroup_v2_path(monkeypatch, cgroup_v2)

    assert cgroup_memory_limit_bytes() is None


def test_cgroup_memory_limit_bytes_none_when_no_cgroup_files(monkeypatch, tmp_path: Path):
    missing = tmp_path / "does-not-exist"
    monkeypatch.setattr("ci.ndgeojsons_to_parquet.Path", lambda p: missing)

    assert cgroup_memory_limit_bytes() is None


def test_duckdb_memory_limit_uses_cgroup_limit_over_host_ram(monkeypatch, tmp_path: Path):
    limit_bytes = 1024**3  # 1 GiB, well below actual host RAM
    cgroup_v2 = tmp_path / "memory.max"
    cgroup_v2.write_text(str(limit_bytes))
    _patch_cgroup_v2_path(monkeypatch, cgroup_v2)

    # duckdb_memory_limit reserves 2GB and floors to whole GB, so a 1GB cgroup
    # limit (less than the 2GB reservation) clamps to the reservation itself.
    assert duckdb_memory_limit() == "2GB"


def test_duckdb_memory_limit_falls_back_to_host_ram_without_cgroup(monkeypatch, tmp_path: Path):
    missing = tmp_path / "does-not-exist"
    monkeypatch.setattr("ci.ndgeojsons_to_parquet.Path", lambda p: missing)

    expected_gb = max(psutil.virtual_memory().total - 2 * 1024**3, 2 * 1024**3) // 1024**3
    assert duckdb_memory_limit() == f"{expected_gb}GB"


def test_to_parquet(tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    input_file = Path("./tests/data/dixy_ru.ndgeojson")

    shutil.copy(input_file.absolute(), input_dir.absolute())

    out_dir = tmp_path / "output"
    out_dir.mkdir()
    output_parquet = out_dir / "output.parquet"

    to_parquet(input_dir, output_parquet)

    result_df = read_parquet(output_parquet)

    assert len(result_df) == 4
    columns = result_df.columns.tolist()
    expected_top_level_columns = ["id", "type", "dataset_attributes", "properties", "geom", "bbox"]
    assert all(col in columns for col in expected_top_level_columns)
    # TODO: better GeoParquet file validation


def test_salvaged_geojson_features_reach_parquet(tmp_path: Path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    features = [json.loads(line) for line in Path("tests/data/dixy_ru.ndgeojson").read_text().splitlines()]
    dataset_attributes = features[0]["dataset_attributes"]
    header = {"type": "FeatureCollection", "dataset_attributes": dataset_attributes}
    body = ",\n".join(json.dumps({k: v for k, v in f.items() if k != "dataset_attributes"}) for f in features)
    (input_dir / "example.geojson").write_text(
        json.dumps(header)[:-1] + ',"features":[\n' + body + ',\n{"type":"Feature",', encoding="utf-8"
    )
    (input_dir / "example.ndgeojson").write_text("", encoding="utf-8")

    repair_directory(input_dir)
    output_parquet = tmp_path / "output.parquet"
    to_parquet(input_dir, output_parquet)

    result_df = read_parquet(output_parquet)
    assert sorted(result_df["id"]) == sorted(f["id"] for f in features)
    assert all(dict(attrs) == dataset_attributes for attrs in result_df["dataset_attributes"])
