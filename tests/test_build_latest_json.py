import json

from ci.build_latest_json import build_latest_json


def test_basic_latest_json(tmp_path):
    """Build latest.json from two group manifests."""
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    brands_manifest = {
        "group": "brands",
        "updated_at": "2026-04-16T14:00:00Z",
        "run_id": "2026-04-16-14-00-00",
        "spiders": {
            "mcdonalds": {
                "run_id": "2026-04-16-14-00-00",
                "ran_at": "2026-04-16T14:31:12Z",
                "geojson_url": "https://example.com/runs/brands/2026-04-16-14-00-00/output/mcdonalds.geojson",
                "stats_url": "https://example.com/runs/brands/2026-04-16-14-00-00/stats/mcdonalds.json",
                "feature_count": 100,
                "error_count": 0,
                "elapsed_time": 42.5,
            },
        },
    }

    infra_manifest = {
        "group": "infrastructure",
        "updated_at": "2026-03-01T10:00:00Z",
        "run_id": "2026-03-01-10-00-00",
        "spiders": {
            "511_nl_ca": {
                "run_id": "2026-03-01-10-00-00",
                "ran_at": "2026-03-01T10:15:00Z",
                "geojson_url": "https://example.com/runs/infrastructure/2026-03-01-10-00-00/output/511_nl_ca.geojson",
                "stats_url": "https://example.com/runs/infrastructure/2026-03-01-10-00-00/stats/511_nl_ca.json",
                "feature_count": 50,
                "error_count": 0,
                "elapsed_time": 10.0,
            },
        },
    }

    (manifests_dir / "brands.manifest.json").write_text(json.dumps(brands_manifest))
    (manifests_dir / "infrastructure.manifest.json").write_text(json.dumps(infra_manifest))

    url_prefix = "https://example.com"

    latest = build_latest_json(manifests_dir, url_prefix)

    assert latest["spiders"] == 2
    assert latest["total_lines"] == 150
    assert len(latest["groups"]) == 2

    brands_group = next(g for g in latest["groups"] if g["name"] == "brands")
    assert brands_group["spider_count"] == 1
    assert brands_group["feature_count"] == 100
    assert "zip_url" in brands_group
    assert "parquet_url" in brands_group
    assert "pmtiles_url" in brands_group

    infra_group = next(g for g in latest["groups"] if g["name"] == "infrastructure")
    assert infra_group["spider_count"] == 1


def test_duplicate_spider_in_two_manifests(tmp_path):
    """If a spider appears in two manifests, the more recent ran_at wins."""
    manifests_dir = tmp_path / "manifests"
    manifests_dir.mkdir()

    manifest_a = {
        "group": "brands",
        "updated_at": "2026-04-16T14:00:00Z",
        "run_id": "2026-04-16-14-00-00",
        "spiders": {
            "dupe_spider": {
                "run_id": "2026-04-16-14-00-00",
                "ran_at": "2026-04-16T14:31:12Z",
                "geojson_url": "https://example.com/brands/dupe_spider.geojson",
                "stats_url": "https://example.com/brands/dupe_spider.json",
                "feature_count": 100,
                "error_count": 0,
                "elapsed_time": 42.5,
            },
        },
    }

    manifest_b = {
        "group": "infrastructure",
        "updated_at": "2026-03-01T10:00:00Z",
        "run_id": "2026-03-01-10-00-00",
        "spiders": {
            "dupe_spider": {
                "run_id": "2026-03-01-10-00-00",
                "ran_at": "2026-03-01T10:15:00Z",
                "geojson_url": "https://example.com/infra/dupe_spider.geojson",
                "stats_url": "https://example.com/infra/dupe_spider.json",
                "feature_count": 50,
                "error_count": 0,
                "elapsed_time": 10.0,
            },
        },
    }

    (manifests_dir / "brands.manifest.json").write_text(json.dumps(manifest_a))
    (manifests_dir / "infrastructure.manifest.json").write_text(json.dumps(manifest_b))

    latest = build_latest_json(manifests_dir, "https://example.com")

    # Only counted once, from the more recent manifest (brands)
    assert latest["spiders"] == 1
    assert latest["total_lines"] == 100
