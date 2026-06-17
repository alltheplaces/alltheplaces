# Grouped Spider Runs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run spider groups at independent cadences with per-group download artifacts, replacing the monolithic weekly `run_all_spiders.sh`.

**Architecture:** Reuse the existing `Lineage` enum (`locations/extensions/add_lineage.py`) to classify spiders into five groups (brands, addresses, aggregators, government, infrastructure). A new scrapy command lists spiders by group. A new `ci/run_group_spiders.sh` runs one group at a time, producing per-group zip/parquet/pmtiles. A lightweight `ci/assemble_latest.sh` merges all group manifests into the global `latest.json` and updates S3 redirects.

**Tech Stack:** Python 3.11, Scrapy, bash, jq, tippecanoe, duckdb (via existing `ndgeojsons_to_parquet.py`), AWS CLI (S3 + R2)

**Spec:** `docs/superpowers/specs/2026-04-11-grouped-spider-runs-design.md`

**Key discovery:** The codebase already has `Lineage` enum + `spider_class_to_lineage()` that resolves group from filesystem path with a `lineage` class-attribute override. The spec's `run_group` attribute IS the existing `lineage` attribute. No new spider attribute needed.

---

### Task 1: Add group name mapping to Lineage enum

**Files:**
- Modify: `locations/extensions/add_lineage.py`
- Modify: `tests/test_lineage.py`

- [ ] **Step 1: Write failing tests for group property**

Add to `tests/test_lineage.py`:

```python
from locations.extensions.add_lineage import Lineage, spider_class_to_lineage, VALID_GROUPS, lineage_for_group


def test_lineage_group_names():
    assert Lineage.Brands.group == "brands"
    assert Lineage.Addresses.group == "addresses"
    assert Lineage.Aggregators.group == "aggregators"
    assert Lineage.Governments.group == "government"
    assert Lineage.Infrastructure.group == "infrastructure"
    assert Lineage.Unknown.group == "brands"


def test_valid_groups():
    assert VALID_GROUPS == {"brands", "addresses", "aggregators", "government", "infrastructure"}


def test_lineage_for_group():
    assert lineage_for_group("brands") == Lineage.Brands
    assert lineage_for_group("addresses") == Lineage.Addresses
    assert lineage_for_group("aggregators") == Lineage.Aggregators
    assert lineage_for_group("government") == Lineage.Governments
    assert lineage_for_group("infrastructure") == Lineage.Infrastructure


def test_lineage_for_group_invalid():
    import pytest
    with pytest.raises(ValueError, match="Unknown group"):
        lineage_for_group("invalid_group")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_lineage.py -v`
Expected: FAIL — `VALID_GROUPS` and `lineage_for_group` not defined, `Lineage.Brands.group` doesn't exist

- [ ] **Step 3: Implement group property on Lineage**

In `locations/extensions/add_lineage.py`, add a `group` property to `Lineage` and the helper constants/functions:

```python
class Lineage(Enum):
    Addresses = "S_ATP_ADDRESSES"
    Aggregators = "S_ATP_AGGREGATORS"
    Brands = "S_ATP_BRANDS"
    Governments = "S_ATP_GOVERNMENTS"
    Infrastructure = "S_ATP_INFRASTRUCTURE"
    Unknown = "S_?"

    @property
    def group(self) -> str:
        return _LINEAGE_TO_GROUP.get(self, "brands")


_LINEAGE_TO_GROUP = {
    Lineage.Addresses: "addresses",
    Lineage.Aggregators: "aggregators",
    Lineage.Brands: "brands",
    Lineage.Governments: "government",
    Lineage.Infrastructure: "infrastructure",
    Lineage.Unknown: "brands",
}

_GROUP_TO_LINEAGE = {v: k for k, v in _LINEAGE_TO_GROUP.items() if k != Lineage.Unknown}

VALID_GROUPS = set(_GROUP_TO_LINEAGE.keys())


def lineage_for_group(group: str) -> Lineage:
    if group not in _GROUP_TO_LINEAGE:
        raise ValueError(f"Unknown group: {group!r}. Valid groups: {sorted(VALID_GROUPS)}")
    return _GROUP_TO_LINEAGE[group]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_lineage.py -v`
Expected: All tests PASS (both new and existing)

- [ ] **Step 5: Commit**

```bash
git add locations/extensions/add_lineage.py tests/test_lineage.py
git commit -m "Add group name mapping to Lineage enum"
```

---

### Task 2: Add `scrapy list_group` command

**Files:**
- Create: `locations/commands/list_group.py`
- Create: `tests/test_list_group_command.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_list_group_command.py`:

```python
import sys

from locations.extensions.add_lineage import Lineage, spider_class_to_lineage, VALID_GROUPS


def test_spider_group_resolution_from_path():
    """Verify that spiders in subdirectories resolve to the correct group."""
    from locations.spiders.infrastructure.aurora_city_council_traffic_signals_us import (
        AuroraCityCouncilTrafficSignalsUSSpider,
    )

    assert spider_class_to_lineage(AuroraCityCouncilTrafficSignalsUSSpider).group == "infrastructure"


def test_spider_group_resolution_brands_default():
    """Verify that top-level spiders default to brands."""
    from locations.spiders.greggs_gb import GreggsGBSpider

    assert spider_class_to_lineage(GreggsGBSpider).group == "brands"


def test_spider_group_override_via_lineage():
    """Verify that the lineage class attribute overrides path-based resolution."""
    from locations.spiders.greggs_gb import GreggsGBSpider

    original = getattr(GreggsGBSpider, "lineage", None)
    try:
        GreggsGBSpider.lineage = Lineage.Infrastructure
        assert spider_class_to_lineage(GreggsGBSpider).group == "infrastructure"
    finally:
        if original is None:
            del GreggsGBSpider.lineage
        else:
            GreggsGBSpider.lineage = original


def test_all_groups_have_at_least_one_spider():
    """Verify every defined group has at least one spider in the codebase."""
    from locations.exporters.geojson import iter_spider_classes_in_modules

    groups_seen = set()
    for spider_class in iter_spider_classes_in_modules():
        lineage = spider_class_to_lineage(spider_class)
        groups_seen.add(lineage.group)

    for group in VALID_GROUPS:
        assert group in groups_seen, f"No spiders found for group {group!r}"
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/test_list_group_command.py -v`
Expected: All PASS (these test existing infrastructure, not the command itself yet)

- [ ] **Step 3: Write the `list_group` command**

Create `locations/commands/list_group.py`:

```python
import argparse
import sys

from scrapy.commands import ScrapyCommand
from scrapy.exceptions import UsageError

from locations.extensions.add_lineage import VALID_GROUPS, lineage_for_group, spider_class_to_lineage


class ListGroupCommand(ScrapyCommand):
    requires_project = True
    default_settings = {"LOG_ENABLED": False}

    def syntax(self) -> str:
        return "<group>"

    def short_desc(self) -> str:
        return "List spiders belonging to a run group"

    def long_desc(self) -> str:
        groups = ", ".join(sorted(VALID_GROUPS))
        return f"List spider names belonging to the given run group. Valid groups: {groups}"

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        if len(args) != 1:
            raise UsageError()

        group = args[0]
        try:
            lineage_for_group(group)
        except ValueError as e:
            sys.stderr.write(str(e) + "\n")
            self.exitcode = 1
            return

        if not self.crawler_process:
            raise RuntimeError("Crawler process not defined")

        for spider_name in sorted(self.crawler_process.spider_loader.list()):
            spidercls = self.crawler_process.spider_loader.load(spider_name)
            spider_lineage = spider_class_to_lineage(spidercls)
            if spider_lineage.group == group:
                sys.stdout.write(f"{spider_name}\n")
```

- [ ] **Step 4: Test the command manually**

Run: `uv run scrapy list_group brands 2>/dev/null | head -5`
Expected: First 5 brand spider names, one per line

Run: `uv run scrapy list_group infrastructure 2>/dev/null | wc -l`
Expected: A number around 358

Run: `uv run scrapy list_group invalid_group 2>/dev/null`
Expected: Error message on stderr, exit code 1

- [ ] **Step 5: Verify all groups sum to total spider count**

Run: `uv run scrapy list -s LOG_ENABLED=False | wc -l` and compare with:
```bash
total=0; for g in brands addresses aggregators government infrastructure; do count=$(uv run scrapy list_group $g 2>/dev/null | wc -l); echo "$g: $count"; total=$((total + count)); done; echo "total: $total"
```
Expected: Totals match

- [ ] **Step 6: Commit**

```bash
git add locations/commands/list_group.py tests/test_list_group_command.py
git commit -m "Add scrapy list_group command for filtering spiders by run group"
```

---

### Task 3: Create `ci/build_group_manifest.py`

**Files:**
- Create: `ci/build_group_manifest.py`
- Create: `tests/test_build_group_manifest.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_build_group_manifest.py`:

```python
import json
from pathlib import Path

from ci.build_group_manifest import build_manifest


def test_fresh_manifest_from_successful_spiders(tmp_path):
    """First run: no previous manifest, all spiders succeed."""
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()
    (stats_dir / "mcdonalds.json").write_text(json.dumps({"item_scraped_count": 100, "log_count/ERROR": 0, "elapsed_time_seconds": 42.5}))
    (stats_dir / "burger_king.json").write_text(json.dumps({"item_scraped_count": 50, "log_count/ERROR": 1, "elapsed_time_seconds": 30.0}))

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
    assert manifest["spiders"]["mcdonalds"]["geojson_url"] == "https://example.com/runs/brands/2026-04-16-14-00-00/output/mcdonalds.geojson"
    assert "burger_king" in manifest["spiders"]


def test_failed_spider_keeps_previous_entry(tmp_path):
    """Spider fails: previous entry preserved."""
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()
    # mcdonalds succeeds
    (stats_dir / "mcdonalds.json").write_text(json.dumps({"item_scraped_count": 100, "elapsed_time_seconds": 42.5}))
    # burger_king has no stats file (crashed before writing stats)

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

    # burger_king keeps the old entry
    assert manifest["spiders"]["burger_king"]["run_id"] == "2026-04-09-14-00-00"
    assert manifest["spiders"]["burger_king"]["feature_count"] == 50
    # mcdonalds gets the new entry
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
        spider_names=["mcdonalds"],  # old_deleted_spider not in list
        stats_dir=stats_dir,
        previous_manifest=previous_manifest,
    )

    assert "old_deleted_spider" not in manifest["spiders"]
    assert "mcdonalds" in manifest["spiders"]


def test_never_run_spider_absent(tmp_path):
    """Spider has never succeeded: not in manifest."""
    stats_dir = tmp_path / "stats"
    stats_dir.mkdir()
    # new_spider has no stats file

    manifest = build_manifest(
        group="brands",
        run_id="2026-04-16-14-00-00",
        run_url_prefix="https://example.com/runs/brands/2026-04-16-14-00-00",
        spider_names=["new_spider"],
        stats_dir=stats_dir,
        previous_manifest=None,
    )

    assert "new_spider" not in manifest["spiders"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_build_group_manifest.py -v`
Expected: FAIL — `ci.build_group_manifest` module not found

- [ ] **Step 3: Implement `build_group_manifest.py`**

Create `ci/build_group_manifest.py`:

```python
import json
from datetime import datetime, timezone
from pathlib import Path


def build_manifest(
    group: str,
    run_id: str,
    run_url_prefix: str,
    spider_names: list[str],
    stats_dir: Path,
    previous_manifest: dict | None,
) -> dict:
    """Build a group manifest by merging current run results with previous manifest.

    Spiders that succeeded (non-zero item_scraped_count) get fresh entries.
    Spiders that failed or produced zero items keep their previous entry.
    Spiders no longer in the group are dropped.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    previous_spiders = (previous_manifest or {}).get("spiders", {})
    spider_names_set = set(spider_names)
    spiders = {}

    for spider_name in spider_names:
        stats_file = stats_dir / f"{spider_name}.json"

        if stats_file.exists():
            try:
                stats = json.loads(stats_file.read_text())
            except (json.JSONDecodeError, OSError):
                stats = {}

            feature_count = stats.get("item_scraped_count", 0) or 0
            error_count = stats.get("log_count/ERROR", 0) or 0
            elapsed_time = stats.get("elapsed_time_seconds", 0) or 0

            if feature_count > 0:
                spiders[spider_name] = {
                    "run_id": run_id,
                    "ran_at": now,
                    "geojson_url": f"{run_url_prefix}/output/{spider_name}.geojson",
                    "stats_url": f"{run_url_prefix}/stats/{spider_name}.json",
                    "feature_count": feature_count,
                    "error_count": error_count,
                    "elapsed_time": elapsed_time,
                }
                continue

        # Spider failed or produced zero items: keep previous entry if it exists
        if spider_name in previous_spiders:
            spiders[spider_name] = previous_spiders[spider_name]

    return {
        "group": group,
        "updated_at": now,
        "run_id": run_id,
        "spiders": spiders,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build or update a group manifest")
    parser.add_argument("--group", required=True, help="Group name")
    parser.add_argument("--run-id", required=True, help="Run timestamp ID")
    parser.add_argument("--run-url-prefix", required=True, help="URL prefix for this run")
    parser.add_argument("--spider-list", required=True, help="File with spider names, one per line")
    parser.add_argument("--stats-dir", required=True, help="Directory containing per-spider stats JSON files")
    parser.add_argument("--previous-manifest", help="Path to previous manifest JSON file (optional)")
    parser.add_argument("--output", required=True, help="Output manifest file path")

    args = parser.parse_args()

    spider_names = Path(args.spider_list).read_text().strip().splitlines()
    stats_dir = Path(args.stats_dir)

    previous_manifest = None
    if args.previous_manifest and Path(args.previous_manifest).exists():
        previous_manifest = json.loads(Path(args.previous_manifest).read_text())

    manifest = build_manifest(
        group=args.group,
        run_id=args.run_id,
        run_url_prefix=args.run_url_prefix,
        spider_names=spider_names,
        stats_dir=stats_dir,
        previous_manifest=previous_manifest,
    )

    Path(args.output).write_text(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_build_group_manifest.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add ci/build_group_manifest.py tests/test_build_group_manifest.py
git commit -m "Add build_group_manifest.py for manifest merge logic"
```

---

### Task 4: Create `ci/build_latest_json.py`

**Files:**
- Create: `ci/build_latest_json.py`
- Create: `tests/test_build_latest_json.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_build_latest_json.py`:

```python
import json
from pathlib import Path

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_build_latest_json.py -v`
Expected: FAIL — module not found

- [ ] **Step 3: Implement `build_latest_json.py`**

Create `ci/build_latest_json.py`:

```python
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def build_latest_json(manifests_dir: Path, url_prefix: str) -> dict:
    """Merge all group manifests into a single latest.json.

    Args:
        manifests_dir: Directory containing *.manifest.json files.
        url_prefix: Base URL for constructing per-group artifact URLs (e.g. https://alltheplaces-data.openaddresses.io).
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_files = sorted(manifests_dir.glob("*.manifest.json"))

    # Merge all spider entries, resolving duplicates by most recent ran_at
    all_spiders: dict[str, tuple[str, dict]] = {}  # spider_name -> (group, entry)
    group_data: dict[str, dict] = {}  # group_name -> manifest

    for mf in manifest_files:
        try:
            manifest = json.loads(mf.read_text())
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Skipping %s: %s", mf, e)
            continue

        group_name = manifest.get("group", mf.stem.replace(".manifest", ""))
        group_data[group_name] = manifest

        for spider_name, entry in manifest.get("spiders", {}).items():
            if spider_name in all_spiders:
                existing_group, existing_entry = all_spiders[spider_name]
                if entry.get("ran_at", "") > existing_entry.get("ran_at", ""):
                    logger.warning(
                        "Spider %s found in both %s and %s, keeping %s (more recent)",
                        spider_name, existing_group, group_name, group_name,
                    )
                    all_spiders[spider_name] = (group_name, entry)
                else:
                    logger.warning(
                        "Spider %s found in both %s and %s, keeping %s (more recent)",
                        spider_name, existing_group, group_name, existing_group,
                    )
            else:
                all_spiders[spider_name] = (group_name, entry)

    # Build per-group summaries
    groups = []
    for group_name, manifest in sorted(group_data.items()):
        spiders_in_group = {
            name: entry for name, (g, entry) in all_spiders.items() if g == group_name
        }
        spider_count = len(spiders_in_group)
        feature_count = sum(e.get("feature_count", 0) for e in spiders_in_group.values())
        run_id = manifest.get("run_id", "")

        groups.append({
            "name": group_name,
            "spider_count": spider_count,
            "feature_count": feature_count,
            "last_run_time": manifest.get("updated_at", ""),
            "last_run_id": run_id,
            "zip_url": f"{url_prefix}/runs/latest/{group_name}.zip",
            "parquet_url": f"{url_prefix}/runs/latest/{group_name}.parquet",
            "pmtiles_url": f"{url_prefix}/runs/latest/{group_name}.pmtiles",
        })

    total_spiders = len(all_spiders)
    total_lines = sum(entry.get("feature_count", 0) for _, entry in all_spiders.values())

    return {
        "updated_at": now,
        "stats_url": f"{url_prefix}/runs/latest/stats/_results.json",
        "insights_url": f"{url_prefix}/runs/latest/stats/_insights.json",
        "spiders": total_spiders,
        "total_lines": total_lines,
        "groups": groups,
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build latest.json from group manifests")
    parser.add_argument("--manifests-dir", required=True, help="Directory containing *.manifest.json files")
    parser.add_argument("--url-prefix", required=True, help="Base URL prefix")
    parser.add_argument("--output", required=True, help="Output latest.json path")

    args = parser.parse_args()

    latest = build_latest_json(Path(args.manifests_dir), args.url_prefix)
    Path(args.output).write_text(json.dumps(latest))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_build_latest_json.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add ci/build_latest_json.py tests/test_build_latest_json.py
git commit -m "Add build_latest_json.py to merge group manifests into latest.json"
```

---

### Task 5: Create `ci/run_group_spiders.sh`

**Files:**
- Create: `ci/run_group_spiders.sh`

This is adapted from `ci/run_all_spiders.sh`. The differences are: (1) takes a group argument, (2) uses group-scoped S3 paths, (3) uses `scrapy list_group` instead of `scrapy list`, (4) generates per-group zip/parquet/pmtiles, (5) builds the group manifest, (6) invokes the assembler.

- [ ] **Step 1: Create the script**

Create `ci/run_group_spiders.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# --- Validate arguments ---
RUN_GROUP="${1:-}"
if [ -z "${RUN_GROUP}" ]; then
    (>&2 echo "Usage: run_group_spiders.sh <group>")
    (>&2 echo "Valid groups: addresses, aggregators, brands, government, infrastructure")
    exit 1
fi

echo "git revision: ${GIT_COMMIT:-unknown}"
echo "run group: ${RUN_GROUP}"

if [ -z "${S3_BUCKET}" ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

if [ -z "${GITHUB_WORKSPACE}" ]; then
    (>&2 echo "Please set GITHUB_WORKSPACE environment variable")
    exit 1
fi

# --- Timestamps and paths (group-scoped) ---
RUN_START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
RUN_TIMESTAMP=$(date -u +%F-%H-%M-%S)
RUN_KEY_PREFIX="runs/${RUN_GROUP}/${RUN_TIMESTAMP}"
RUN_S3_PREFIX="s3://${S3_BUCKET}/${RUN_KEY_PREFIX}"
RUN_R2_PREFIX="s3://${R2_BUCKET}/${RUN_KEY_PREFIX}"
RUN_URL_PREFIX="https://alltheplaces-data.openaddresses.io/${RUN_KEY_PREFIX}"
SPIDER_RUN_DIR="${GITHUB_WORKSPACE}/output"
PARALLELISM=${PARALLELISM:-12}
SPIDER_TIMEOUT=${SPIDER_TIMEOUT:-28800}

mkdir -p "${SPIDER_RUN_DIR}"

# --- List spiders in this group ---
(>&2 echo "Listing spiders in group ${RUN_GROUP}")
uv run scrapy list_group "${RUN_GROUP}" -s REQUESTS_CACHE_ENABLED=False > "${SPIDER_RUN_DIR}/spider_list.txt"

while IFS= read -r spider; do
    echo "timeout -k 15m 495m uv run scrapy crawl --output ${SPIDER_RUN_DIR}/output/${spider}.geojson:geojson --output ${SPIDER_RUN_DIR}/output/${spider}.ndgeojson:ndgeojson --logfile ${SPIDER_RUN_DIR}/logs/${spider}.txt --loglevel ERROR --set TELNETCONSOLE_ENABLED=0 --set CLOSESPIDER_TIMEOUT=${SPIDER_TIMEOUT} --set LOGSTATS_FILE=${SPIDER_RUN_DIR}/stats/${spider}.json ${spider}" >> "${SPIDER_RUN_DIR}/commands.txt"
done < "${SPIDER_RUN_DIR}/spider_list.txt"

mkdir -p "${SPIDER_RUN_DIR}/logs"
mkdir -p "${SPIDER_RUN_DIR}/stats"
mkdir -p "${SPIDER_RUN_DIR}/output"
SPIDER_COUNT=$(wc -l < "${SPIDER_RUN_DIR}/commands.txt" | tr -d ' ')

# --- Slack notification ---
if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
    (>&2 echo "Skipping Slack notification because SLACK_WEBHOOK_URL not set")
else
    curl -X POST \
         --silent \
         -H 'Content-type: application/json' \
         --data "{\"text\": \"Starting ${RUN_GROUP} run ${RUN_TIMESTAMP} with ${SPIDER_COUNT} spiders\"}" \
         "${SLACK_WEBHOOK_URL}"

    trap '{
        retval=$?
        if [ $retval -eq 0 ]; then
            curl -X POST \
                 --silent \
                 -H "Content-type: application/json" \
                 --data "{\"text\": \"${RUN_GROUP} run ${RUN_TIMESTAMP} completed successfully with ${SPIDER_COUNT} spiders\"}" \
                 "${SLACK_WEBHOOK_URL}"
        else
            curl -X POST \
                 --silent \
                 -H "Content-type: application/json" \
                 --data "{\"text\": \"${RUN_GROUP} run ${RUN_TIMESTAMP} failed with exit code ${retval} with ${SPIDER_COUNT} spiders\"}" \
                 "${SLACK_WEBHOOK_URL}"
        fi
    }' EXIT
fi

# --- Run spiders in parallel ---
(>&2 echo "Running ${SPIDER_COUNT} ${RUN_GROUP} spiders ${PARALLELISM} at a time")
xargs -t -L 1 -P "${PARALLELISM}" -a "${SPIDER_RUN_DIR}/commands.txt" -i sh -c "{} || true"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "xargs failed with exit code ${retval}")
    exit 1
fi
(>&2 echo "Done running ${RUN_GROUP} spiders")

OUTPUT_LINECOUNT=$(cat "${SPIDER_RUN_DIR}"/output/*.geojson 2>/dev/null | wc -l | tr -d ' ')
(>&2 echo "Generated ${OUTPUT_LINECOUNT} lines")

# --- Generate per-group pmtiles ---
tippecanoe --cluster-distance=25 \
           --drop-rate=1 \
           --maximum-zoom=15 \
           --cluster-maxzoom=g \
           --maximum-tile-bytes=10000000 \
           --layer="alltheplaces" \
           --read-parallel \
           --attribution="<a href=\"https://www.alltheplaces.xyz/\">All the Places</a> ${RUN_GROUP} ${RUN_TIMESTAMP}" \
           -o "${SPIDER_RUN_DIR}/${RUN_GROUP}.pmtiles" \
           "${SPIDER_RUN_DIR}"/output/*.geojson \
           2>&1 | grep -v -E '^\s*[0-9]+\.[0-9]+%\s|^Reordering geometry:\s*[0-9]|^Read [0-9]+\.[0-9]+ million features|^Sorting\.\.\.' >&2
retval=${PIPESTATUS[0]}
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't generate pmtiles for ${RUN_GROUP}")
    include_pmtiles=false
else
    (>&2 echo "Done generating ${RUN_GROUP} pmtiles")
    include_pmtiles=true
fi

# --- Generate per-group parquet ---
uv run python ci/ndgeojsons_to_parquet.py \
    --directory "${SPIDER_RUN_DIR}/output" \
    --output "${SPIDER_RUN_DIR}/${RUN_GROUP}.parquet"
retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't create parquet for ${RUN_GROUP}")
    include_parquet=false
else
    include_parquet=true
fi

# Clean up ndgeojson files
rm -f "${SPIDER_RUN_DIR}"/output/*.ndgeojson
(>&2 echo "Done creating ${RUN_GROUP} parquet")

# --- Generate per-group zip ---
(>&2 echo "Compressing ${RUN_GROUP} output files")
(cd "${SPIDER_RUN_DIR}" && zip -qr "${RUN_GROUP}.zip" output)

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't zip ${RUN_GROUP} output")
    exit 1
fi

# --- Write per-spider stats summary ---
(>&2 echo "Writing ${RUN_GROUP} summary JSON")
echo "{\"count\": ${SPIDER_COUNT}, \"results\": []}" > "${SPIDER_RUN_DIR}/stats/_results.json"
while IFS= read -r spider; do
    statistics_json="${SPIDER_RUN_DIR}/stats/${spider}.json"

    if [ ! -f "${statistics_json}" ]; then
        (>&2 echo "Couldn't find ${statistics_json}")
        continue
    fi

    feature_count=$(jq --raw-output '.item_scraped_count' "${statistics_json}")
    if [ "$?" -ne 0 ] || [ "${feature_count}" == "null" ]; then
        feature_count="0"
    fi

    error_count=$(jq --raw-output '."log_count/ERROR"' "${statistics_json}")
    if [ "$?" -ne 0 ] || [ "${error_count}" == "null" ]; then
        error_count="0"
    fi

    elapsed_time=$(jq --raw-output '.elapsed_time_seconds' "${statistics_json}")
    if [ "$?" -ne 0 ] || [ "${elapsed_time}" == "null" ]; then
        elapsed_time="0"
    fi

    spider_filename=$(uv run scrapy spider_filename "${spider}")

    jq --compact-output \
        --arg spider_name "${spider}" \
        --arg spider_feature_count ${feature_count} \
        --arg spider_error_count ${error_count} \
        --arg spider_elapsed_time ${elapsed_time} \
        --arg spider_filename ${spider_filename} \
        '.results += [{"spider": $spider_name, "filename": $spider_filename, "errors": $spider_error_count | tonumber, "features": $spider_feature_count | tonumber, "elapsed_time": $spider_elapsed_time | tonumber}]' \
        "${SPIDER_RUN_DIR}/stats/_results.json" > "${SPIDER_RUN_DIR}/stats/_results.json.tmp"
    mv "${SPIDER_RUN_DIR}/stats/_results.json.tmp" "${SPIDER_RUN_DIR}/stats/_results.json"
done < "${SPIDER_RUN_DIR}/spider_list.txt"
(>&2 echo "Wrote ${RUN_GROUP} summary JSON")

# --- Sync to S3 ---
(>&2 echo "Saving ${RUN_GROUP} files to ${RUN_S3_PREFIX}")
uv run aws s3 sync \
    --only-show-errors \
    "${SPIDER_RUN_DIR}/" \
    "${RUN_S3_PREFIX}/"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't sync ${RUN_GROUP} to S3")
    exit 1
fi

# --- Sync to R2 ---
(>&2 echo "Saving ${RUN_GROUP} files to ${RUN_R2_PREFIX}")
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
uv run aws s3 sync \
    --endpoint-url="${R2_ENDPOINT_URL}" \
    --only-show-errors \
    "${SPIDER_RUN_DIR}/" \
    "${RUN_R2_PREFIX}/"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't sync ${RUN_GROUP} to R2")
    exit 1
fi

# --- Write per-group latest.json ---
RUN_END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUTPUT_FILESIZE=$(du -b "${SPIDER_RUN_DIR}/${RUN_GROUP}.zip" | awk '{ print $1 }')

jq -n --compact-output \
    --arg run_id "${RUN_TIMESTAMP}" \
    --arg run_group "${RUN_GROUP}" \
    --arg run_zip_url "${RUN_URL_PREFIX}/${RUN_GROUP}.zip" \
    --arg run_pmtiles_url "${RUN_URL_PREFIX}/${RUN_GROUP}.pmtiles" \
    --arg run_parquet_url "${RUN_URL_PREFIX}/${RUN_GROUP}.parquet" \
    --arg run_stats_url "${RUN_URL_PREFIX}/stats/_results.json" \
    --arg run_start_time "${RUN_START}" \
    --arg run_end_time "${RUN_END}" \
    --arg run_output_size "${OUTPUT_FILESIZE}" \
    --arg run_spider_count "${SPIDER_COUNT}" \
    --arg run_line_count "${OUTPUT_LINECOUNT}" \
    '{"run_id": $run_id, "group": $run_group, "zip_url": $run_zip_url, "pmtiles_url": $run_pmtiles_url, "parquet_url": $run_parquet_url, "stats_url": $run_stats_url, "start_time": $run_start_time, "end_time": $run_end_time, "size_bytes": $run_output_size | tonumber, "spiders": $run_spider_count | tonumber, "total_lines": $run_line_count | tonumber}' \
    > "${SPIDER_RUN_DIR}/group_latest.json"

GROUP_S3_PREFIX="s3://${S3_BUCKET}/runs/${RUN_GROUP}"
GROUP_R2_PREFIX="s3://${R2_BUCKET}/runs/${RUN_GROUP}"

uv run aws s3 cp --only-show-errors "${SPIDER_RUN_DIR}/group_latest.json" "${GROUP_S3_PREFIX}/latest.json"
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
    uv run aws s3 --endpoint-url="${R2_ENDPOINT_URL}" cp --only-show-errors "${SPIDER_RUN_DIR}/group_latest.json" "${GROUP_R2_PREFIX}/latest.json"

# --- Append to per-group history.json ---
uv run aws s3 cp --only-show-errors "${GROUP_S3_PREFIX}/history.json" "${SPIDER_RUN_DIR}/group_history.json" 2>/dev/null || echo '[]' > "${SPIDER_RUN_DIR}/group_history.json"
if [ ! -s "${SPIDER_RUN_DIR}/group_history.json" ]; then
    echo '[]' > "${SPIDER_RUN_DIR}/group_history.json"
fi

jq --compact-output \
    --argjson latest "$(<"${SPIDER_RUN_DIR}/group_latest.json")" \
    '. += [$latest]' "${SPIDER_RUN_DIR}/group_history.json" > "${SPIDER_RUN_DIR}/group_history.json.tmp"
mv "${SPIDER_RUN_DIR}/group_history.json.tmp" "${SPIDER_RUN_DIR}/group_history.json"

uv run aws s3 cp --only-show-errors "${SPIDER_RUN_DIR}/group_history.json" "${GROUP_S3_PREFIX}/history.json"
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
    uv run aws s3 --endpoint-url="${R2_ENDPOINT_URL}" cp --only-show-errors "${SPIDER_RUN_DIR}/group_history.json" "${GROUP_R2_PREFIX}/history.json"

# --- Build group manifest ---
(>&2 echo "Building ${RUN_GROUP} manifest")
MANIFEST_S3_PATH="s3://${S3_BUCKET}/runs/latest/${RUN_GROUP}.manifest.json"
uv run aws s3 cp --only-show-errors "${MANIFEST_S3_PATH}" "${SPIDER_RUN_DIR}/previous_manifest.json" 2>/dev/null || true

uv run python ci/build_group_manifest.py \
    --group "${RUN_GROUP}" \
    --run-id "${RUN_TIMESTAMP}" \
    --run-url-prefix "${RUN_URL_PREFIX}" \
    --spider-list "${SPIDER_RUN_DIR}/spider_list.txt" \
    --stats-dir "${SPIDER_RUN_DIR}/stats" \
    --previous-manifest "${SPIDER_RUN_DIR}/previous_manifest.json" \
    --output "${SPIDER_RUN_DIR}/manifest.json"

uv run aws s3 cp --only-show-errors "${SPIDER_RUN_DIR}/manifest.json" "${MANIFEST_S3_PATH}"
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
    uv run aws s3 --endpoint-url="${R2_ENDPOINT_URL}" cp --only-show-errors "${SPIDER_RUN_DIR}/manifest.json" "s3://${R2_BUCKET}/runs/latest/${RUN_GROUP}.manifest.json"
(>&2 echo "Saved ${RUN_GROUP} manifest")

# --- Invoke assembler ---
(>&2 echo "Invoking assembler")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"${SCRIPT_DIR}/assemble_latest.sh"
```

- [ ] **Step 2: Make executable**

Run: `chmod +x ci/run_group_spiders.sh`

- [ ] **Step 3: Commit**

```bash
git add ci/run_group_spiders.sh
git commit -m "Add run_group_spiders.sh for running spider groups independently"
```

---

### Task 6: Create `ci/assemble_latest.sh`

**Files:**
- Create: `ci/assemble_latest.sh`

The assembler is lightweight: it merges manifests into `latest.json`, downloads per-spider geojsons for insights, builds global `_results.json`, updates S3 redirects, and purges CDN.

- [ ] **Step 1: Create the script**

Create `ci/assemble_latest.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

if [ -z "${S3_BUCKET}" ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

ASSEMBLY_DIR="${GITHUB_WORKSPACE}/assembly"
MANIFESTS_DIR="${ASSEMBLY_DIR}/manifests"
STATS_DIR="${ASSEMBLY_DIR}/stats"
OUTPUT_DIR="${ASSEMBLY_DIR}/output"
URL_PREFIX="https://alltheplaces-data.openaddresses.io"
PARALLELISM=${PARALLELISM:-12}

mkdir -p "${MANIFESTS_DIR}" "${STATS_DIR}" "${OUTPUT_DIR}"

# --- Download all group manifests ---
(>&2 echo "Downloading group manifests")
uv run aws s3 sync \
    --only-show-errors \
    --exclude "*" \
    --include "*.manifest.json" \
    "s3://${S3_BUCKET}/runs/latest/" \
    "${MANIFESTS_DIR}/"

MANIFEST_COUNT=$(ls "${MANIFESTS_DIR}"/*.manifest.json 2>/dev/null | wc -l | tr -d ' ')
if [ "${MANIFEST_COUNT}" -eq 0 ]; then
    (>&2 echo "No group manifests found. Nothing to assemble.")
    exit 1
fi
(>&2 echo "Found ${MANIFEST_COUNT} group manifests")

# --- Build global latest.json ---
(>&2 echo "Building latest.json")
uv run python ci/build_latest_json.py \
    --manifests-dir "${MANIFESTS_DIR}" \
    --url-prefix "${URL_PREFIX}" \
    --output "${ASSEMBLY_DIR}/latest.json"

# --- Build global _results.json from all manifests ---
(>&2 echo "Building global _results.json")

# Collect all spider entries from all manifests into a single results file
TOTAL_SPIDERS=0
echo '{"count": 0, "results": []}' > "${STATS_DIR}/_results.json"

for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
    group_name=$(jq -r '.group' "${manifest_file}")

    for spider_name in $(jq -r '.spiders | keys[]' "${manifest_file}"); do
        stats_url=$(jq -r --arg s "${spider_name}" '.spiders[$s].stats_url' "${manifest_file}")
        ran_at=$(jq -r --arg s "${spider_name}" '.spiders[$s].ran_at' "${manifest_file}")
        run_id=$(jq -r --arg s "${spider_name}" '.spiders[$s].run_id' "${manifest_file}")
        feature_count=$(jq -r --arg s "${spider_name}" '.spiders[$s].feature_count' "${manifest_file}")
        error_count=$(jq -r --arg s "${spider_name}" '.spiders[$s].error_count' "${manifest_file}")
        elapsed_time=$(jq -r --arg s "${spider_name}" '.spiders[$s].elapsed_time' "${manifest_file}")

        # Compute data age in days
        ran_at_epoch=$(date -d "${ran_at}" +%s 2>/dev/null || date -j -f "%Y-%m-%dT%H:%M:%SZ" "${ran_at}" +%s 2>/dev/null || echo 0)
        now_epoch=$(date +%s)
        data_age_days=$(( (now_epoch - ran_at_epoch) / 86400 ))

        jq --compact-output \
            --arg spider "${spider_name}" \
            --arg group "${group_name}" \
            --arg last_run_time "${ran_at}" \
            --arg last_run_id "${run_id}" \
            --argjson features "${feature_count}" \
            --argjson errors "${error_count}" \
            --argjson elapsed "${elapsed_time}" \
            --argjson age "${data_age_days}" \
            '.results += [{"spider": $spider, "run_group": $group, "features": $features, "errors": $errors, "elapsed_time": $elapsed, "last_run_time": $last_run_time, "last_run_id": $last_run_id, "data_age_days": $age}]' \
            "${STATS_DIR}/_results.json" > "${STATS_DIR}/_results.json.tmp"
        mv "${STATS_DIR}/_results.json.tmp" "${STATS_DIR}/_results.json"

        TOTAL_SPIDERS=$((TOTAL_SPIDERS + 1))
    done
done

# Update the count
jq --compact-output --argjson count "${TOTAL_SPIDERS}" '.count = $count' \
    "${STATS_DIR}/_results.json" > "${STATS_DIR}/_results.json.tmp"
mv "${STATS_DIR}/_results.json.tmp" "${STATS_DIR}/_results.json"
(>&2 echo "Built _results.json with ${TOTAL_SPIDERS} spiders")

# --- Download per-spider geojsons for insights ---
(>&2 echo "Downloading per-spider geojsons for insights")
for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
    for spider_name in $(jq -r '.spiders | keys[]' "${manifest_file}"); do
        geojson_url=$(jq -r --arg s "${spider_name}" '.spiders[$s].geojson_url' "${manifest_file}")
        # Convert URL to S3 path
        s3_key=$(echo "${geojson_url}" | sed "s|${URL_PREFIX}/||")
        echo "uv run aws s3 cp --only-show-errors s3://${S3_BUCKET}/${s3_key} ${OUTPUT_DIR}/${spider_name}.geojson"
    done
done > "${ASSEMBLY_DIR}/download_commands.txt"

xargs -L 1 -P "${PARALLELISM}" -a "${ASSEMBLY_DIR}/download_commands.txt" -i sh -c "{} || true"
(>&2 echo "Downloaded geojsons")

# --- Run insights ---
uv run scrapy insights --atp-nsi-osm "${OUTPUT_DIR}" --outfile "${STATS_DIR}/_insights.json"
(>&2 echo "Done comparing against Name Suggestion Index and OpenStreetMap")

# --- Upload stats ---
uv run aws s3 sync --only-show-errors "${STATS_DIR}/" "s3://${S3_BUCKET}/runs/latest/stats/"
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
    uv run aws s3 --endpoint-url="${R2_ENDPOINT_URL}" sync --only-show-errors "${STATS_DIR}/" "s3://${R2_BUCKET}/runs/latest/stats/"
(>&2 echo "Uploaded stats")

# --- Upload latest.json ---
uv run aws s3 cp --only-show-errors "${ASSEMBLY_DIR}/latest.json" "s3://${S3_BUCKET}/runs/latest.json"
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
    uv run aws s3 --endpoint-url="${R2_ENDPOINT_URL}" cp --only-show-errors "${ASSEMBLY_DIR}/latest.json" "s3://${R2_BUCKET}/runs/latest.json"
(>&2 echo "Saved latest.json")

# --- Append to global history.json ---
uv run aws s3 cp --only-show-errors "s3://${S3_BUCKET}/runs/history.json" "${ASSEMBLY_DIR}/history.json" 2>/dev/null || echo '[]' > "${ASSEMBLY_DIR}/history.json"
if [ ! -s "${ASSEMBLY_DIR}/history.json" ]; then
    echo '[]' > "${ASSEMBLY_DIR}/history.json"
fi

jq --compact-output \
    --argjson latest "$(<"${ASSEMBLY_DIR}/latest.json")" \
    '. += [$latest]' "${ASSEMBLY_DIR}/history.json" > "${ASSEMBLY_DIR}/history.json.tmp"
mv "${ASSEMBLY_DIR}/history.json.tmp" "${ASSEMBLY_DIR}/history.json"

uv run aws s3 cp --only-show-errors "${ASSEMBLY_DIR}/history.json" "s3://${S3_BUCKET}/runs/history.json"
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
    uv run aws s3 --endpoint-url="${R2_ENDPOINT_URL}" cp --only-show-errors "${ASSEMBLY_DIR}/history.json" "s3://${R2_BUCKET}/runs/history.json"
(>&2 echo "Saved history.json")

# --- Update per-group artifact redirects ---
touch "${ASSEMBLY_DIR}/placeholder.txt"

for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
    group_name=$(jq -r '.group' "${manifest_file}")
    group_run_id=$(jq -r '.run_id' "${manifest_file}")
    group_run_prefix="${URL_PREFIX}/runs/${group_name}/${group_run_id}"

    for ext in zip parquet pmtiles; do
        uv run aws s3 cp --only-show-errors \
            --website-redirect="${group_run_prefix}/${group_name}.${ext}" \
            "${ASSEMBLY_DIR}/placeholder.txt" \
            "s3://${S3_BUCKET}/runs/latest/${group_name}.${ext}"
    done
done
(>&2 echo "Updated per-group artifact redirects")

# --- Update per-spider geojson redirects ---
for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
    for spider_name in $(jq -r '.spiders | keys[]' "${manifest_file}"); do
        geojson_url=$(jq -r --arg s "${spider_name}" '.spiders[$s].geojson_url' "${manifest_file}")

        uv run aws s3 cp --only-show-errors \
            --website-redirect="${geojson_url}" \
            "${ASSEMBLY_DIR}/placeholder.txt" \
            "s3://${S3_BUCKET}/runs/latest/output/${spider_name}.geojson"

        AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
        AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
        uv run aws s3 \
            --endpoint-url="${R2_ENDPOINT_URL}" \
            cp --only-show-errors \
            --website-redirect="${geojson_url}" \
            "${ASSEMBLY_DIR}/placeholder.txt" \
            "s3://${R2_BUCKET}/runs/latest/output/${spider_name}.geojson"
    done
done
(>&2 echo "Updated per-spider geojson redirects")

# --- Write info_embed.html (static fallback) ---
(>&2 echo "Writing info_embed.html")
EMBED_ROWS=""
for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
    group_name=$(jq -r '.group' "${manifest_file}")
    spider_count=$(jq '.spiders | length' "${manifest_file}")
    feature_count=$(jq '[.spiders[].feature_count] | add // 0' "${manifest_file}")
    EMBED_ROWS="${EMBED_ROWS}<tr><td>${group_name}</td><td>${spider_count} spiders, $(printf "%'d" "${feature_count}") rows</td><td><a href=\"${URL_PREFIX}/runs/latest/${group_name}.zip\">zip</a></td></tr>"
done

cat > "${ASSEMBLY_DIR}/info_embed.html" << EOF
<html><body>
<table>
<tr><th>Group</th><th>Data</th><th>Download</th></tr>
${EMBED_ROWS}
</table>
<small>Updated $(date)</small>
</body></html>
EOF

uv run aws s3 cp --only-show-errors \
    --content-type "text/html; charset=utf-8" \
    "${ASSEMBLY_DIR}/info_embed.html" \
    "s3://${S3_BUCKET}/runs/latest/info_embed.html"
(>&2 echo "Saved info_embed.html")

# --- Purge CDN ---
if [ -z "${BUNNY_API_KEY:-}" ]; then
    (>&2 echo "Skipping CDN purge because BUNNY_API_KEY not set")
else
    for path in "runs%2Flatest.json" "runs%2Fhistory.json" "runs%2Flatest%2Foutput%2F%2A"; do
        curl --request GET \
             --silent \
             --url "https://api.bunny.net/purge?url=https%3A%2F%2Falltheplaces.b-cdn.net%2F${path}&async=false" \
             --header "AccessKey: ${BUNNY_API_KEY}" \
             --header 'accept: application/json'
    done
    (>&2 echo "Purged CDN cache")
fi

(>&2 echo "Assembly complete")
```

- [ ] **Step 2: Make executable**

Run: `chmod +x ci/assemble_latest.sh`

- [ ] **Step 3: Commit**

```bash
git add ci/assemble_latest.sh
git commit -m "Add assemble_latest.sh for merging group manifests into global latest.json"
```

---

### Task 7: Verify and clean up

**Files:**
- Modify: `ci/run_all_spiders.sh` (no changes yet — kept for rollback)
- Run all tests

- [ ] **Step 1: Run the full test suite**

Run: `uv run pytest tests/ -v`
Expected: All tests pass including the new ones

- [ ] **Step 2: Lint check**

Run: `uv run pre-commit run --all-files`
Expected: All checks pass

- [ ] **Step 3: Verify list_group command covers all spiders**

Run:
```bash
total=0
for g in brands addresses aggregators government infrastructure; do
    count=$(uv run scrapy list_group $g 2>/dev/null | wc -l | tr -d ' ')
    echo "$g: $count"
    total=$((total + count))
done
echo "total: $total"
all=$(uv run scrapy list -s LOG_ENABLED=False | wc -l | tr -d ' ')
echo "scrapy list: $all"
```
Expected: `total` equals `scrapy list` count

- [ ] **Step 4: Commit any lint fixes**

```bash
git add -u
git commit -m "Fix lint issues"
```

---

### Notes for operational phases (not code tasks)

**Phase 2 (bootstrap):** Run each group manually:
```bash
ci/run_group_spiders.sh brands
ci/run_group_spiders.sh addresses
ci/run_group_spiders.sh aggregators
ci/run_group_spiders.sh government
ci/run_group_spiders.sh infrastructure
```

**Phase 3 (update consumers):** Update the Cloudflare Worker and alltheplaces.xyz map viewer to read the new `latest.json` schema (these are separate repos).

**Phase 4 (cutover):** Change ECS scheduled task from `run_all_spiders.sh` to `run_group_spiders.sh brands`.

**Phase 5 (add schedules):** Add ECS scheduled tasks for the other four groups.

**Phase 6 (cleanup):** Delete `ci/run_all_spiders.sh`.
