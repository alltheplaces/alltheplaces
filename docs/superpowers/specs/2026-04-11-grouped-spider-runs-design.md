# Grouped Spider Runs

Run different categories of spiders at different cadences, producing per-group download artifacts.

## Problem

All ~4,200 spiders run together once a week. Address and infrastructure spiders produce stable data that doesn't need weekly refreshes, while brand/POI spiders benefit from frequent updates. Running everything together wastes compute and proxy budget on data that rarely changes.

## Groups

Five named groups: `brands`, `addresses`, `aggregators`, `government`, `infrastructure`.

### Membership resolution

1. If a spider class defines `run_group = "<name>"`, that value is used.
2. Otherwise, group is inferred from the spider's filesystem path:
   - `locations/spiders/addresses/...` -> `addresses`
   - `locations/spiders/aggregators/...` -> `aggregators`
   - `locations/spiders/government/...` -> `government`
   - `locations/spiders/infrastructure/...` -> `infrastructure`
   - Everything else -> `brands`

The `run_group` attribute is the exception mechanism. Most spiders rely on the path default.

### Scrapy command

A new command, `scrapy list_group <group>`, prints spider names belonging to a group. It errors if any spider has `run_group` set to an unknown group name (typo protection). Lives at `locations/commands/list_group.py`.

## Per-group run script

`ci/run_group_spiders.sh <group>` is the generalized successor to `run_all_spiders.sh`. It takes one positional argument: the group name.

### What it does

1. **Sets up group-scoped paths.** Output lands at `runs/<group>/<timestamp>/...` in S3/R2 (e.g. `runs/brands/2026-04-11-14-00-00/output/mcdonalds.geojson`).

2. **Lists spiders** via `uv run scrapy list_group <group>` and builds `commands.txt` with one `scrapy crawl` per spider, run in parallel via xargs (same parallelism model as today).

3. **Slack notifications** include the group name for attribution.

4. **Per-spider stats summarization** produces `runs/<group>/<timestamp>/stats/_results.json`. The NSI/OSM insights step is NOT run here (only at assembly time).

5. **Generates per-group bundled artifacts** from the local spider output:
   - `<group>.zip` — all geojsons for this group
   - `<group>.parquet` — parquet for this group (via on-the-fly geojson-to-ndgeojson conversion, then `ndgeojsons_to_parquet.py`)
   - `<group>.pmtiles` — tippecanoe over this group's geojsons (same flags as today's combined pmtiles)

6. **Syncs to S3 and R2** under the group-scoped prefix.

7. **Writes `runs/<group>/latest.json`** describing this group's run. Appends to `runs/<group>/history.json`.

8. **Builds the group manifest** at `runs/latest/<group>.manifest.json` (see next section).

9. **Invokes the assembler** as the final step: `ci/assemble_latest.sh`.

### What it does NOT do

- Does not write to the global `runs/latest.json` or `runs/latest/output/<spider>.geojson` redirects. Those are exclusively the assembler's responsibility.
- Does not produce per-group `logs.zip`. Per-spider logs remain at `runs/<group>/<timestamp>/logs/<spider>.txt` and are accessible directly from S3.

### Scheduling

Each group is an ECS scheduled task in the AWS console, configured with whatever cadence is appropriate. The code does not enforce cadence. Recommended starting cadences (documentation only):

- `brands`: weekly
- `government`: monthly
- `aggregators`: monthly
- `addresses`: quarterly
- `infrastructure`: quarterly

## Group manifest

Each group maintains a manifest at `runs/latest/<group>.manifest.json`. This is the cross-run state that lets the assembler know what to bundle.

### Schema

```json
{
  "group": "brands",
  "updated_at": "2026-04-11T14:23:00Z",
  "run_id": "2026-04-11-14-00-00",
  "spiders": {
    "mcdonalds": {
      "run_id": "2026-04-11-14-00-00",
      "ran_at": "2026-04-11T14:31:12Z",
      "geojson_url": "https://alltheplaces-data.openaddresses.io/runs/brands/2026-04-11-14-00-00/output/mcdonalds.geojson",
      "stats_url": "https://alltheplaces-data.openaddresses.io/runs/brands/2026-04-11-14-00-00/stats/mcdonalds.json",
      "feature_count": 38291,
      "error_count": 0,
      "elapsed_time": 412.7
    }
  }
}
```

### Manifest merge logic

At the end of each group run:

1. Download the existing manifest from S3 (treat 404 as `{"spiders": {}}`).
2. For each spider the run was supposed to execute:
   - If the spider produced a geojson AND its stats show non-zero `item_scraped_count`: write a fresh entry pointing at this run's URLs.
   - Otherwise: leave the previous entry untouched (keep last known good data).
3. Drop entries for spiders that no longer belong to this group (deleted, or moved to another group via `run_group` override).
4. Update `group`, `updated_at`, `run_id` at the top level.
5. Upload the new manifest to S3 + R2.

A spider that has never successfully run simply doesn't appear in any manifest. It enters on its first successful run.

### Concurrency

Each group writes only its own manifest file. Two concurrent group runs cannot race on the same object.

## Assembler

`ci/assemble_latest.sh` is invoked at the end of every group run. It is a lightweight script — all heavy artifact generation (zip, parquet, pmtiles) is done by the group runner. The assembler's job is to merge state across groups and update global pointers.

### Steps

1. **Download all group manifests** from `runs/latest/*.manifest.json`. Merge into a flat dict of `{spider_name -> entry}`. If a spider appears in two manifests (shouldn't happen normally), the more recent `ran_at` wins and a warning is logged.

2. **Download per-spider stats** from S3 using the S3 key derived from each manifest entry's `stats_url` (same AWS account, so uses `aws s3 cp` for speed and zero egress cost). Use `xargs -P` for parallelism.

3. **Build global `stats/_results.json`** from all manifests, with existing fields plus:
   - `last_run_time` (from manifest `ran_at`)
   - `last_run_id` (from manifest `run_id`)
   - `run_group` (which group produced this spider)
   - `data_age_days` (computed: `now - ran_at`)

4. **Run insights** across all groups: download per-spider geojsons from S3 (using manifest URLs), then `scrapy insights --atp-nsi-osm` to produce `stats/_insights.json`.

5. **Upload stats** to `runs/latest/stats/` in S3 + R2.

6. **Write global `runs/latest.json`** (schema below).

7. **Append to `runs/history.json`**.

8. **Update `runs/latest/` redirects:**
   - Per-group: `<group>.zip`, `<group>.parquet`, `<group>.pmtiles` for each group, pointing at that group's latest run dir
   - Per-spider: `output/<spider>.geojson` for every spider across all manifests, pointing at the spider's source group run dir

9. **Write `runs/latest/info_embed.html`** as a static fallback (per-group download links).

10. **Purge Bunny CDN** for `latest.json`, `history.json`, and `latest/output/*`.

### Concurrency

Two groups finishing near-simultaneously could both invoke the assembler. The failure mode is benign: one assembler overwrites the other's near-identical output. Both read the same manifests (one group's manifest was just written; the other's is still the previous version). The result is correct either way; the "losing" assembler's output is simply superseded.

## `runs/latest.json` schema

This is a breaking change from the current schema. The combined `output_url`, `pmtiles_url`, and `parquet_url` fields are removed. The `groups` array is now the primary way to access data. Top-level aggregate fields (`spiders`, `total_lines`) remain as sums for convenience.

```json
{
  "updated_at": "2026-04-11T15:00:00Z",
  "stats_url": "https://.../.../stats/_results.json",
  "insights_url": "https://.../.../stats/_insights.json",
  "spiders": 4206,
  "total_lines": 12345678,

  "groups": [
    {
      "name": "brands",
      "spider_count": 3791,
      "feature_count": 9876543,
      "last_run_time": "2026-04-11T14:00:00Z",
      "last_run_id": "2026-04-11-14-00-00",
      "zip_url": "https://.../.../brands.zip",
      "parquet_url": "https://.../.../brands.parquet",
      "pmtiles_url": "https://.../.../brands.pmtiles"
    },
    {
      "name": "addresses",
      "spider_count": 31,
      "feature_count": 2345678,
      "last_run_time": "2026-03-15T10:00:00Z",
      "last_run_id": "2026-03-15-10-00-00",
      "zip_url": "https://.../.../addresses.zip",
      "parquet_url": "https://.../.../addresses.parquet",
      "pmtiles_url": "https://.../.../addresses.pmtiles"
    }
  ]
}
```

`spiders` and `total_lines` at the top level are sums across all groups. Per-group `last_run_time` exposes data freshness. Per-spider freshness is in `_results.json` entries.

Consumers that previously read `output_url` or `pmtiles_url` from `latest.json` will need to be updated to iterate over `groups` instead. Known consumers: the Cloudflare Worker (info embed), the alltheplaces.xyz map viewer, and any third-party scripts using the API.

## Migration plan

### Phase 1 — Code lands, nothing runs in production

- Add `run_group` class attribute support (no spiders use it yet).
- Add the `scrapy list_group` command + tests.
- Create `ci/run_group_spiders.sh` and `ci/assemble_combined_output.sh`.
- The existing `ci/run_all_spiders.sh` and weekly ECS task are untouched.

Safe to merge; nothing changes in production.

### Phase 2 — Manual bootstrap of group manifests

- Run each group manually (one-shot ECS task or local) to populate `runs/latest/<group>.manifest.json`. Brands first (hours), then the others (fast).
- Invoke `ci/assemble_combined_output.sh` writing to a staging prefix (`runs-staging/...`) to verify output sanity against the most recent production run.
- Production `runs/latest.json` is untouched.

### Phase 3 — Update consumers

- Update the Cloudflare Worker to read `groups` from `latest.json` and render per-group download links.
- Update the alltheplaces.xyz map viewer to read per-group `pmtiles_url` entries and add the group selector UI.
- Deploy both before cutover so they're ready when the new `latest.json` schema goes live.

### Phase 4 — Cutover

- Flip the assembler to write to the real `runs/` prefix.
- Change the weekly ECS scheduled task from `run_all_spiders.sh` to `run_group_spiders.sh brands`.
- The next weekly run produces a brands run + assembly. The new `latest.json` schema goes live; the updated Cloudflare Worker and map viewer consume it.

### Phase 5 — Add slower schedules

- Add new ECS scheduled tasks for `addresses`, `aggregators`, `government`, `infrastructure` at their respective cadences.

### Phase 6 — Cleanup

- Delete `ci/run_all_spiders.sh`.
- Update contributor documentation.

### Failure modes

- **Group run fails partway (Phase 2+).** Re-run it; the manifest merge preserves whatever succeeded previously.
- **Assembler fails (Phase 3+).** Production `runs/latest.json` is not updated (assembler hadn't reached that step). Previous `latest.json` stays. Slack notification fires.
- **Group runner fails (Phase 3+).** That group's manifest isn't updated. The assembler runs against previous manifests, producing output identical to the last successful assembly. Stable, no downtime.

## Info embed and Cloudflare Worker

The alltheplaces.xyz website loads an iframe from `https://data.alltheplaces.xyz/runs/latest/info_embed.html`. This HTML is currently generated by `run_all_spiders.sh` as a simple static file, but a Cloudflare Worker reads `latest.json` to serve it.

With groups, the embed shows per-group download options. The Cloudflare Worker reads `latest.json`, iterates over the `groups` array, and renders a download link for each group's zip. Each group row shows:

- Group name
- Spider count and feature count
- Data age (derived from `last_run_time`)
- Download link (zip)

There is no combined "Download All" link. Users download the groups they need.

The assembler also writes a static `info_embed.html` as a fallback with per-group download links. The Cloudflare Worker's dynamic rendering from `latest.json` is the primary path; the static file is the fallback if the Worker is down.

## Map viewer

The map at alltheplaces.xyz currently loads a single `output.pmtiles` layer. With per-group pmtiles, the viewer gains a layer selector that lets users switch between groups.

The viewer reads `latest.json`, discovers the per-group `pmtiles_url` entries, and renders a control (e.g. a dropdown or checkbox group) with one entry per group. `brands` is selected by default (it's the largest and most commonly viewed group).

Switching layers swaps the pmtiles source. Only one pmtiles source is loaded at a time (not overlaid) to keep memory usage reasonable.

The per-group pmtiles URLs come from `latest.json`, so the viewer doesn't need to know the group names at build time. A new group added later automatically appears in the selector.

## Out of scope / follow-up work

- **`ci/dead_spider_killer.py`**: May need adjustment. Its time-based logic ("hasn't been touched in N days") needs to account for non-weekly cadences. The spider-output-based logic ("0 features") still works unchanged.
- **Third-party consumers of `latest.json`**: The schema is breaking (combined artifact URLs removed). Any external scripts reading `output_url` or `pmtiles_url` from the top level will need updating. Consider announcing the change in advance.
