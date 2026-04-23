import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


def build_latest_json(manifests_dir: Path, url_prefix: str) -> dict:
    """Merge all group manifests into a single latest.json.

    Args:
        manifests_dir: Directory containing *.manifest.json files.
        url_prefix: Base URL for constructing per-group artifact URLs.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_files = sorted(manifests_dir.glob("*.manifest.json"))

    all_spiders: dict[str, tuple[str, dict]] = {}
    group_data: dict[str, dict] = {}

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
                        spider_name,
                        existing_group,
                        group_name,
                        group_name,
                    )
                    all_spiders[spider_name] = (group_name, entry)
                else:
                    logger.warning(
                        "Spider %s found in both %s and %s, keeping %s (more recent)",
                        spider_name,
                        existing_group,
                        group_name,
                        existing_group,
                    )
            else:
                all_spiders[spider_name] = (group_name, entry)

    groups = []
    for group_name, manifest in sorted(group_data.items()):
        spiders_in_group = {name: entry for name, (g, entry) in all_spiders.items() if g == group_name}
        spider_count = len(spiders_in_group)
        feature_count = sum(e.get("feature_count", 0) for e in spiders_in_group.values())
        run_id = manifest.get("run_id", "")

        groups.append(
            {
                "name": group_name,
                "spider_count": spider_count,
                "feature_count": feature_count,
                "last_run_time": manifest.get("updated_at", ""),
                "last_run_id": run_id,
                "zip_url": f"{url_prefix}/runs/latest/{group_name}.zip",
                "parquet_url": f"{url_prefix}/runs/latest/{group_name}.parquet",
                "pmtiles_url": f"{url_prefix}/runs/latest/{group_name}.pmtiles",
            }
        )

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
    parser = argparse.ArgumentParser(description="Build latest.json from group manifests")
    parser.add_argument("--manifests-dir", required=True, help="Directory containing *.manifest.json files")
    parser.add_argument("--url-prefix", required=True, help="Base URL prefix")
    parser.add_argument("--output", required=True, help="Output latest.json path")

    args = parser.parse_args()

    latest = build_latest_json(Path(args.manifests_dir), args.url_prefix)
    Path(args.output).write_text(json.dumps(latest))


if __name__ == "__main__":
    main()
