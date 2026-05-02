#!/usr/bin/env bash
set -euo pipefail

if [ -z "${S3_BUCKET:-}" ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

if [ -z "${R2_BUCKET:-}" ]; then
    (>&2 echo "Please set R2_BUCKET environment variable")
    exit 1
fi

if [ -z "${R2_ENDPOINT_URL:-}" ]; then
    (>&2 echo "Please set R2_ENDPOINT_URL environment variable")
    exit 1
fi

if [ -z "${R2_ACCESS_KEY_ID:-}" ]; then
    (>&2 echo "Please set R2_ACCESS_KEY_ID environment variable")
    exit 1
fi

if [ -z "${R2_SECRET_ACCESS_KEY:-}" ]; then
    (>&2 echo "Please set R2_SECRET_ACCESS_KEY environment variable")
    exit 1
fi

if [ -z "${GITHUB_WORKSPACE:-}" ]; then
    (>&2 echo "Please set GITHUB_WORKSPACE environment variable")
    exit 1
fi

URL_PREFIX="https://alltheplaces-data.openaddresses.io"
WORK_DIR="${GITHUB_WORKSPACE}/assemble"
MANIFESTS_DIR="${WORK_DIR}/manifests"
STATS_DIR="${WORK_DIR}/stats"
OUTPUT_DIR="${WORK_DIR}/output"
DOWNLOAD_PARALLELISM=${DOWNLOAD_PARALLELISM:-12}

mkdir -p "${MANIFESTS_DIR}" "${STATS_DIR}" "${OUTPUT_DIR}"

# ──────────────────────────────────────────────
# Step 1: Download all group manifest files
# ──────────────────────────────────────────────
(>&2 echo "Downloading manifest files from S3")
uv run aws s3 sync \
    --only-show-errors \
    --exclude "*" \
    --include "*.manifest.json" \
    "s3://${S3_BUCKET}/runs/latest/" \
    "${MANIFESTS_DIR}/"

MANIFEST_COUNT=$(ls "${MANIFESTS_DIR}"/*.manifest.json 2>/dev/null | wc -l | tr -d ' ')
if [ "${MANIFEST_COUNT}" -eq 0 ]; then
    (>&2 echo "No manifest files found, nothing to assemble")
    exit 1
fi
(>&2 echo "Downloaded ${MANIFEST_COUNT} manifest files")

# ──────────────────────────────────────────────
# Step 2: Merge manifests into latest.json
# ──────────────────────────────────────────────
(>&2 echo "Building latest.json from manifests")
uv run python ci/build_latest_json.py \
    --manifests-dir "${MANIFESTS_DIR}" \
    --url-prefix "${URL_PREFIX}" \
    --output "${WORK_DIR}/latest.json"

(>&2 echo "Built latest.json")

# ──────────────────────────────────────────────
# Step 3: Build global stats/_results.json
# ──────────────────────────────────────────────
(>&2 echo "Building _results.json from manifests")

NOW_EPOCH=$(date +%s)

# Start with an empty results array
echo '{"count": 0, "results": []}' > "${STATS_DIR}/_results.json"

for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
    group_name=$(jq -r '.group // empty' "${manifest_file}")
    run_id=$(jq -r '.run_id // empty' "${manifest_file}")
    updated_at=$(jq -r '.updated_at // empty' "${manifest_file}")

    # Iterate each spider in this manifest
    for spider_name in $(jq -r '.spiders | keys[]' "${manifest_file}"); do
        spider_entry=$(jq -c --arg s "${spider_name}" '.spiders[$s]' "${manifest_file}")

        feature_count=$(echo "${spider_entry}" | jq -r '.feature_count // 0')
        error_count=$(echo "${spider_entry}" | jq -r '.error_count // 0')
        elapsed_time=$(echo "${spider_entry}" | jq -r '.elapsed_time // 0')
        ran_at=$(echo "${spider_entry}" | jq -r '.ran_at // empty')

        # Compute data_age_days
        data_age_days=0
        if [ -n "${ran_at}" ]; then
            ran_at_epoch=$(date -d "${ran_at}" +%s 2>/dev/null || date -jf "%Y-%m-%dT%H:%M:%SZ" "${ran_at}" +%s 2>/dev/null || echo "0")
            if [ "${ran_at_epoch}" -gt 0 ]; then
                data_age_days=$(( (NOW_EPOCH - ran_at_epoch) / 86400 ))
            fi
        fi

        jq --compact-output \
            --arg spider_name "${spider_name}" \
            --arg spider_feature_count "${feature_count}" \
            --arg spider_error_count "${error_count}" \
            --arg spider_elapsed_time "${elapsed_time}" \
            --arg run_group "${group_name}" \
            --arg last_run_time "${ran_at}" \
            --arg last_run_id "${run_id}" \
            --arg data_age_days "${data_age_days}" \
            '.count += 1 | .results += [{"spider": $spider_name, "features": ($spider_feature_count | tonumber), "errors": ($spider_error_count | tonumber), "elapsed_time": ($spider_elapsed_time | tonumber), "run_group": $run_group, "last_run_time": $last_run_time, "last_run_id": $last_run_id, "data_age_days": ($data_age_days | tonumber)}]' \
            "${STATS_DIR}/_results.json" > "${STATS_DIR}/_results.json.tmp"
        mv "${STATS_DIR}/_results.json.tmp" "${STATS_DIR}/_results.json"
    done
done

SPIDER_COUNT=$(jq '.count' "${STATS_DIR}/_results.json")
(>&2 echo "Built _results.json with ${SPIDER_COUNT} spiders")

# ──────────────────────────────────────────────
# Step 4: Download per-spider geojsons for insights
# ──────────────────────────────────────────────
(>&2 echo "Downloading geojson files for insights")

> "${WORK_DIR}/download_commands.txt"
for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
    for spider_name in $(jq -r '.spiders | keys[]' "${manifest_file}"); do
        geojson_url=$(jq -r --arg s "${spider_name}" '.spiders[$s].geojson_url // empty' "${manifest_file}")
        if [ -n "${geojson_url}" ]; then
            # Convert URL to S3 key: strip the URL prefix to get the path
            s3_key="${geojson_url#${URL_PREFIX}/}"
            echo "uv run aws s3 cp --only-show-errors s3://${S3_BUCKET}/${s3_key} ${OUTPUT_DIR}/${spider_name}.geojson" >> "${WORK_DIR}/download_commands.txt"
        fi
    done
done

DOWNLOAD_COUNT=$(wc -l < "${WORK_DIR}/download_commands.txt" | tr -d ' ')
if [ "${DOWNLOAD_COUNT}" -gt 0 ]; then
    (>&2 echo "Downloading ${DOWNLOAD_COUNT} geojson files ${DOWNLOAD_PARALLELISM} at a time")
    xargs -L 1 -P "${DOWNLOAD_PARALLELISM}" -a "${WORK_DIR}/download_commands.txt" -I{} sh -c "{} || true"
    (>&2 echo "Done downloading geojson files")
else
    (>&2 echo "No geojson files to download")
fi

# ──────────────────────────────────────────────
# Step 5: Run insights
# ──────────────────────────────────────────────
(>&2 echo "Running insights")
uv run scrapy insights --atp-nsi-osm "${OUTPUT_DIR}" --outfile "${STATS_DIR}/_insights.json"
(>&2 echo "Done comparing against Name Suggestion Index and OpenStreetMap")

# ──────────────────────────────────────────────
# Step 6: Upload stats to S3 and R2
# ──────────────────────────────────────────────
(>&2 echo "Uploading stats to S3")
uv run aws s3 sync \
    --only-show-errors \
    "${STATS_DIR}/" \
    "s3://${S3_BUCKET}/runs/latest/stats/"

(>&2 echo "Uploading stats to R2")
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
uv run aws s3 sync \
    --endpoint-url="${R2_ENDPOINT_URL}" \
    --only-show-errors \
    "${STATS_DIR}/" \
    "s3://${R2_BUCKET}/runs/latest/stats/"

(>&2 echo "Done uploading stats")

# ──────────────────────────────────────────────
# Step 7: Upload latest.json to S3 and R2
# ──────────────────────────────────────────────
(>&2 echo "Uploading latest.json to S3")
uv run aws s3 cp \
    --only-show-errors \
    "${WORK_DIR}/latest.json" \
    "s3://${S3_BUCKET}/runs/latest.json"

(>&2 echo "Uploading latest.json to R2")
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
uv run aws s3 \
    --endpoint-url="${R2_ENDPOINT_URL}" \
    cp \
    --only-show-errors \
    "${WORK_DIR}/latest.json" \
    "s3://${R2_BUCKET}/runs/latest.json"

(>&2 echo "Saved latest.json")

# ──────────────────────────────────────────────
# Step 8: Append to global history.json
# ──────────────────────────────────────────────
(>&2 echo "Updating history.json")

uv run aws s3 cp \
    --only-show-errors \
    "s3://${S3_BUCKET}/runs/history.json" \
    "${WORK_DIR}/history.json" || true

if [ ! -s "${WORK_DIR}/history.json" ]; then
    echo '[]' > "${WORK_DIR}/history.json"
fi

jq --compact-output \
    --argjson latest_run_info "$(<"${WORK_DIR}/latest.json")" \
    '. += [$latest_run_info]' "${WORK_DIR}/history.json" > "${WORK_DIR}/history.json.tmp"
mv "${WORK_DIR}/history.json.tmp" "${WORK_DIR}/history.json"

uv run aws s3 cp \
    --only-show-errors \
    "${WORK_DIR}/history.json" \
    "s3://${S3_BUCKET}/runs/history.json"

AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
uv run aws s3 \
    --endpoint-url="${R2_ENDPOINT_URL}" \
    cp \
    --only-show-errors \
    "${WORK_DIR}/history.json" \
    "s3://${R2_BUCKET}/runs/history.json"

(>&2 echo "Saved history.json")

# ──────────────────────────────────────────────
# Step 9: Update per-group artifact redirects
# ──────────────────────────────────────────────
(>&2 echo "Updating per-group artifact redirects")

touch "${WORK_DIR}/latest_placeholder.txt"

for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
    group_name=$(jq -r '.group // empty' "${manifest_file}")
    run_id=$(jq -r '.run_id // empty' "${manifest_file}")

    if [ -z "${group_name}" ] || [ -z "${run_id}" ]; then
        continue
    fi

    group_run_url="${URL_PREFIX}/runs/${group_name}/${run_id}"

    for ext in zip parquet pmtiles; do
        uv run aws s3 cp \
            --only-show-errors \
            --website-redirect="${group_run_url}/${group_name}.${ext}" \
            "${WORK_DIR}/latest_placeholder.txt" \
            "s3://${S3_BUCKET}/runs/latest/${group_name}.${ext}" || \
            (>&2 echo "Couldn't update latest/${group_name}.${ext} redirect")
    done
done

(>&2 echo "Done updating per-group artifact redirects")

# ──────────────────────────────────────────────
# Step 10: Update per-spider geojson redirects
# ──────────────────────────────────────────────
(>&2 echo "Updating per-spider geojson redirects")

for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
    for spider_name in $(jq -r '.spiders | keys[]' "${manifest_file}"); do
        geojson_url=$(jq -r --arg s "${spider_name}" '.spiders[$s].geojson_url // empty' "${manifest_file}")
        if [ -z "${geojson_url}" ]; then
            continue
        fi

        uv run aws s3 cp \
            --only-show-errors \
            --website-redirect="${geojson_url}" \
            "${WORK_DIR}/latest_placeholder.txt" \
            "s3://${S3_BUCKET}/runs/latest/output/${spider_name}.geojson" || \
            (>&2 echo "Couldn't update latest/output/${spider_name}.geojson redirect in S3")

        AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
        AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
        uv run aws s3 \
            --endpoint-url="${R2_ENDPOINT_URL}" \
            cp \
            --only-show-errors \
            --website-redirect="${geojson_url}" \
            "${WORK_DIR}/latest_placeholder.txt" \
            "s3://${R2_BUCKET}/runs/latest/output/${spider_name}.geojson" || \
            (>&2 echo "Couldn't update latest/output/${spider_name}.geojson redirect in R2")
    done
done

(>&2 echo "Done updating per-spider geojson redirects")

# ──────────────────────────────────────────────
# Step 11: Write info_embed.html
# ──────────────────────────────────────────────
(>&2 echo "Writing info_embed.html")

{
    echo '<html><body>'
    echo '<table>'
    echo '<tr><th>Group</th><th>Spiders</th><th>Features</th><th>Download</th></tr>'

    for manifest_file in "${MANIFESTS_DIR}"/*.manifest.json; do
        group_name=$(jq -r '.group // empty' "${manifest_file}")
        spider_count=$(jq -r '.spiders | length' "${manifest_file}")
        feature_count=$(jq -r '[.spiders[].feature_count // 0] | add // 0' "${manifest_file}")

        echo "<tr><td>${group_name}</td><td>${spider_count}</td><td>${feature_count}</td><td><a href=\"${URL_PREFIX}/runs/latest/${group_name}.zip\">zip</a></td></tr>"
    done

    echo '</table>'
    echo "<small>Updated $(date)</small>"
    echo '</body></html>'
} > "${WORK_DIR}/info_embed.html"

uv run aws s3 cp \
    --only-show-errors \
    --content-type "text/html; charset=utf-8" \
    "${WORK_DIR}/info_embed.html" \
    "s3://${S3_BUCKET}/runs/latest/info_embed.html"

(>&2 echo "Saved info_embed.html")

# ──────────────────────────────────────────────
# Step 12: Purge CDN
# ──────────────────────────────────────────────
if [ -z "${BUNNY_API_KEY:-}" ]; then
    (>&2 echo "Skipping CDN cache purge because BUNNY_API_KEY environment variable not set")
else
    curl --request GET \
         --silent \
         --url 'https://api.bunny.net/purge?url=https%3A%2F%2Falltheplaces.b-cdn.net%2Fruns%2Flatest.json&async=false' \
         --header "AccessKey: ${BUNNY_API_KEY}" \
         --header 'accept: application/json'
    (>&2 echo "Purged latest.json from CDN")

    curl --request GET \
         --silent \
         --url 'https://api.bunny.net/purge?url=https%3A%2F%2Falltheplaces.b-cdn.net%2Fruns%2Fhistory.json&async=false' \
         --header "AccessKey: ${BUNNY_API_KEY}" \
         --header 'accept: application/json'
    (>&2 echo "Purged history.json from CDN")

    curl --request GET \
         --silent \
         --url 'https://api.bunny.net/purge?url=https%3A%2F%2Falltheplaces.b-cdn.net%2Fruns%2Flatest%2Foutput%2F%2A&async=false' \
         --header "AccessKey: ${BUNNY_API_KEY}" \
         --header 'accept: application/json'
    (>&2 echo "Purged latest/output/* from CDN")
fi

(>&2 echo "Assembly complete")
