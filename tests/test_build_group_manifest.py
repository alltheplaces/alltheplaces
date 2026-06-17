import json

from ci.build_group_manifest import build_manifest


def test_fresh_manifest_from_successful_spiders(tmp_path):
    """First run: no previous manifest, all spiders succeed."""
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()
    (stats_dir / "mcdonalds.json").write_text(
        json.dumps({"item_scraped_count": 100, "log_count/ERROR": 0, "elapsed_time_seconds": 42.5})
    )
    (stats_dir / "burger_king.json").write_text(
        json.dumps({"item_scraped_count": 50, "log_count/ERROR": 1, "elapsed_time_seconds": 30.0})
    )

    manifest = build_manifest(
        group="brands",
        run_id="2026-04-16-14-00-00",
        run_url_prefix="https://example.com/runs/brands/2026-04-16-14-00-00",
        spider_names=["mcdonalds", "burger_king"],
        stats_dir=stats_dir,
        previous_manifest=None,
    )

    assert manifest["group"] == "brands"
    assert manifest["run_id"] == "2026-04-16-14-00-00"
    assert "mcdonalds" in manifest["spiders"]
    assert manifest["spiders"]["mcdonalds"]["feature_count"] == 100
    assert (
        manifest["spiders"]["mcdonalds"]["geojson_url"]
        == "https://example.com/runs/brands/2026-04-16-14-00-00/output/mcdonalds.geojson"
    )
    assert "burger_king" in manifest["spiders"]


def test_failed_spider_keeps_previous_entry(tmp_path):
    """Spider fails: previous entry preserved."""
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()
    (stats_dir / "mcdonalds.json").write_text(json.dumps({"item_scraped_count": 100, "elapsed_time_seconds": 42.5}))

    previous_manifest = {
        "group": "brands",
        "run_id": "2026-04-09-14-00-00",
        "spiders": {
            "burger_king": {
                "run_id": "2026-04-09-14-00-00",
                "ran_at": "2026-04-09T14:10:00Z",
                "geojson_url": "https://example.com/runs/brands/2026-04-09-14-00-00/output/burger_king.geojson",
                "stats_url": "https://example.com/runs/brands/2026-04-09-14-00-00/stats/burger_king.json",
                "feature_count": 50,
                "error_count": 0,
                "elapsed_time": 30.0,
            },
        },
    }

    manifest = build_manifest(
        group="brands",
        run_id="2026-04-16-14-00-00",
        run_url_prefix="https://example.com/runs/brands/2026-04-16-14-00-00",
        spider_names=["mcdonalds", "burger_king"],
        stats_dir=stats_dir,
        previous_manifest=previous_manifest,
    )

    assert manifest["spiders"]["burger_king"]["run_id"] == "2026-04-09-14-00-00"
    assert manifest["spiders"]["burger_king"]["feature_count"] == 50
    assert manifest["spiders"]["mcdonalds"]["run_id"] == "2026-04-16-14-00-00"


def test_zero_items_keeps_previous_entry(tmp_path):
    """Spider produces zero items: previous entry preserved."""
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()
    (stats_dir / "mcdonalds.json").write_text(json.dumps({"item_scraped_count": 0, "elapsed_time_seconds": 5.0}))

    previous_manifest = {
        "group": "brands",
        "run_id": "2026-04-09-14-00-00",
        "spiders": {
            "mcdonalds": {
                "run_id": "2026-04-09-14-00-00",
                "ran_at": "2026-04-09T14:10:00Z",
                "geojson_url": "https://example.com/old/mcdonalds.geojson",
                "stats_url": "https://example.com/old/mcdonalds.json",
                "feature_count": 100,
                "error_count": 0,
                "elapsed_time": 42.5,
            },
        },
    }

    manifest = build_manifest(
        group="brands",
        run_id="2026-04-16-14-00-00",
        run_url_prefix="https://example.com/runs/brands/2026-04-16-14-00-00",
        spider_names=["mcdonalds"],
        stats_dir=stats_dir,
        previous_manifest=previous_manifest,
    )

    assert manifest["spiders"]["mcdonalds"]["run_id"] == "2026-04-09-14-00-00"


def test_deleted_spider_dropped_from_manifest(tmp_path):
    """Spider removed from group: entry dropped."""
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()
    (stats_dir / "mcdonalds.json").write_text(json.dumps({"item_scraped_count": 100, "elapsed_time_seconds": 42.5}))

    previous_manifest = {
        "group": "brands",
        "run_id": "2026-04-09-14-00-00",
        "spiders": {
            "mcdonalds": {
                "run_id": "2026-04-09-14-00-00",
                "ran_at": "2026-04-09T14:10:00Z",
                "geojson_url": "https://example.com/old/mcdonalds.geojson",
                "stats_url": "https://example.com/old/mcdonalds.json",
                "feature_count": 100,
                "error_count": 0,
                "elapsed_time": 42.5,
            },
            "old_deleted_spider": {
                "run_id": "2026-04-09-14-00-00",
                "ran_at": "2026-04-09T14:10:00Z",
                "geojson_url": "https://example.com/old/old_deleted_spider.geojson",
                "stats_url": "https://example.com/old/old_deleted_spider.json",
                "feature_count": 10,
                "error_count": 0,
                "elapsed_time": 5.0,
            },
        },
    }

    manifest = build_manifest(
        group="brands",
        run_id="2026-04-16-14-00-00",
        run_url_prefix="https://example.com/runs/brands/2026-04-16-14-00-00",
        spider_names=["mcdonalds"],
        stats_dir=stats_dir,
        previous_manifest=previous_manifest,
    )

    assert "old_deleted_spider" not in manifest["spiders"]
    assert "mcdonalds" in manifest["spiders"]


def test_never_run_spider_absent(tmp_path):
    """Spider has never succeeded: not in manifest."""
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()

    manifest = build_manifest(
        group="brands",
        run_id="2026-04-16-14-00-00",
        run_url_prefix="https://example.com/runs/brands/2026-04-16-14-00-00",
        spider_names=["new_spider"],
        stats_dir=stats_dir,
        previous_manifest=None,
    )

    assert "new_spider" not in manifest["spiders"]
