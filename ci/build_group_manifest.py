import argparse
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

        if spider_name in previous_spiders:
            spiders[spider_name] = previous_spiders[spider_name]

    return {
        "group": group,
        "updated_at": now,
        "run_id": run_id,
        "spiders": spiders,
    }


def main():

    parser = argparse.ArgumentParser(description="Build or update a group manifest")
    parser.add_argument("--group", required=True, help="Group name")
    parser.add_argument("--run-id", required=True, help="Run timestamp ID")
    parser.add_argument("--run-url-prefix", required=True, help="URL prefix for this run")
    parser.add_argument("--spider-list", required=True, help="File with spider names, one per line")
    parser.add_argument("--stats-dir", required=True, help="Directory containing per-spider stats JSON files")
    parser.add_argument("--previous-manifest", help="Path to previous manifest JSON file (optional)")
    parser.add_argument("--output", required=True, help="Output manifest file path")

    args = parser.parse_args()

    spider_names = [s for s in Path(args.spider_list).read_text().strip().splitlines() if s]
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
