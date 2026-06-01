#!/usr/bin/env bash
set -euo pipefail

RUN_GROUP="${1:-}"
if [ -z "${RUN_GROUP}" ]; then
    (>&2 echo "Usage: $0 <group-name>")
    exit 1
fi

echo "git revision: ${GIT_COMMIT:-unknown}"
echo "Running group: ${RUN_GROUP}"

if [ -z "${S3_BUCKET}" ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

if [ -z "${GITHUB_WORKSPACE}" ]; then
    (>&2 echo "Please set GITHUB_WORKSPACE environment variable")
    exit 1
fi

RUN_START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
RUN_TIMESTAMP=$(date -u +%F-%H-%M-%S)
RUN_KEY_PREFIX="runs/${RUN_GROUP}/${RUN_TIMESTAMP}"
RUN_S3_PREFIX="s3://${S3_BUCKET}/${RUN_KEY_PREFIX}"
RUN_R2_PREFIX="s3://${R2_BUCKET}/${RUN_KEY_PREFIX}"
RUN_URL_PREFIX="https://alltheplaces-data.openaddresses.io/${RUN_KEY_PREFIX}"
SPIDER_RUN_DIR="${GITHUB_WORKSPACE}/output"
PARALLELISM=${PARALLELISM:-12}
SPIDER_TIMEOUT=${SPIDER_TIMEOUT:-28800} # default to 8 hours

mkdir -p "${SPIDER_RUN_DIR}"
mkdir -p "${SPIDER_RUN_DIR}/logs"
mkdir -p "${SPIDER_RUN_DIR}/stats"
mkdir -p "${SPIDER_RUN_DIR}/output"

# Save the spider list for the manifest builder
(>&2 echo "Listing spiders in group ${RUN_GROUP}")
uv run scrapy list_group "${RUN_GROUP}" -s REQUESTS_CACHE_ENABLED=False > "${SPIDER_RUN_DIR}/spider_list.txt"

SPIDER_COUNT=$(wc -l < "${SPIDER_RUN_DIR}/spider_list.txt" | tr -d ' ')
if [ "${SPIDER_COUNT}" -eq 0 ]; then
    (>&2 echo "No spiders found in group ${RUN_GROUP}")
    exit 1
fi

(>&2 echo "Writing to ${SPIDER_RUN_DIR}")
while IFS= read -r spider; do
    echo "timeout -k 15m 495m uv run scrapy crawl --output ${SPIDER_RUN_DIR}/output/${spider}.geojson:geojson --output ${SPIDER_RUN_DIR}/output/${spider}.ndgeojson:ndgeojson --logfile ${SPIDER_RUN_DIR}/logs/${spider}.txt --loglevel ERROR --set TELNETCONSOLE_ENABLED=0 --set CLOSESPIDER_TIMEOUT=${SPIDER_TIMEOUT} --set LOGSTATS_FILE=${SPIDER_RUN_DIR}/stats/${spider}.json ${spider}" >> "${SPIDER_RUN_DIR}/commands.txt"
done < "${SPIDER_RUN_DIR}/spider_list.txt"

# Send a message to Slack that we're starting
if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
    (>&2 echo "Skipping Slack notification because SLACK_WEBHOOK_URL environment variable not set")
else
    curl -X POST \
         --silent \
         -H 'Content-type: application/json' \
         --data "{\"text\": \"Starting group '${RUN_GROUP}' run ${RUN_TIMESTAMP} with ${SPIDER_COUNT} spiders\"}" \
         "${SLACK_WEBHOOK_URL}"

    # Set a hook to send a message to Slack when the job completes, including the exit code
    trap '{
        retval=$?
        if [ $retval -eq 0 ]; then
            curl -X POST \
                 --silent \
                 -H "Content-type: application/json" \
                 --data "{\"text\": \"Group '"'"'${RUN_GROUP}'"'"' run ${RUN_TIMESTAMP} completed successfully with ${SPIDER_COUNT} spiders\"}" \
                 "${SLACK_WEBHOOK_URL}"
        else
            curl -X POST \
                 --silent \
                 -H "Content-type: application/json" \
                 --data "{\"text\": \"Group '"'"'${RUN_GROUP}'"'"' run ${RUN_TIMESTAMP} failed with exit code ${retval} with ${SPIDER_COUNT} spiders\"}" \
                 "${SLACK_WEBHOOK_URL}"
        fi
    }' EXIT
fi

(>&2 echo "Running ${SPIDER_COUNT} spiders ${PARALLELISM} at a time")
xargs -t -L 1 -P "${PARALLELISM}" -a "${SPIDER_RUN_DIR}/commands.txt" -i sh -c "{} || true"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "xargs failed with exit code ${retval}")
    exit 1
fi
(>&2 echo "Done running spiders")

OUTPUT_LINECOUNT=$(cat "${SPIDER_RUN_DIR}"/output/*.geojson | wc -l | tr -d ' ')
(>&2 echo "Generated ${OUTPUT_LINECOUNT} lines")

# Generate pmtiles
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
    (>&2 echo "Couldn't generate pmtiles, won't include in output")
    include_pmtiles=false
else
    (>&2 echo "Done generating pmtiles")
    include_pmtiles=true
fi

# Generate parquet
uv run python ci/ndgeojsons_to_parquet.py \
    --directory "${SPIDER_RUN_DIR}/output" \
    --output "${SPIDER_RUN_DIR}/${RUN_GROUP}.parquet"
retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't create parquet file from ndgeojsons, won't include in output")
    include_parquet=false
else
    include_parquet=true
fi

# Clean up ndgeojson files as they are packed into parquet and no longer needed
rm "${SPIDER_RUN_DIR}"/output/*.ndgeojson

(>&2 echo "Done creating parquet file")

# Summarize stats from spider_list.txt instead of calling scrapy list again
(>&2 echo "Writing out summary JSON")
echo "{\"count\": ${SPIDER_COUNT}, \"results\": []}" >> "${SPIDER_RUN_DIR}/stats/_results.json"
while IFS= read -r spider; do
    statistics_json="${SPIDER_RUN_DIR}/stats/${spider}.json"

    if [ ! -f "${statistics_json}" ]; then
        (>&2 echo "Couldn't find ${statistics_json}")
        continue
    fi

    feature_count=$(jq --raw-output '.item_scraped_count' "${statistics_json}")
    retval=$?
    if [ ! $retval -eq 0 ] || [ "${feature_count}" == "null" ]; then
        feature_count="0"
    fi

    error_count=$(jq --raw-output '."log_count/ERROR"' "${statistics_json}")
    retval=$?
    if [ ! $retval -eq 0 ] || [ "${error_count}" == "null" ]; then
        error_count="0"
    fi

    elapsed_time=$(jq --raw-output '.elapsed_time_seconds' "${statistics_json}")
    retval=$?
    if [ ! $retval -eq 0 ] || [ "${elapsed_time}" == "null" ]; then
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
(>&2 echo "Wrote out summary JSON")

# Create per-group zip
(>&2 echo "Compressing output files")
(cd "${SPIDER_RUN_DIR}" && zip -qr "${RUN_GROUP}.zip" output)

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't zip output dir")
    exit 1
fi

# Sync to S3
(>&2 echo "Saving output files to ${RUN_S3_PREFIX}")
uv run aws s3 sync \
    --only-show-errors \
    "${SPIDER_RUN_DIR}/" \
    "${RUN_S3_PREFIX}/"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't sync to s3")
    exit 1
fi

# Sync to R2
(>&2 echo "Saving output files to ${RUN_R2_PREFIX}")
AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
uv run aws s3 sync \
    --endpoint-url="${R2_ENDPOINT_URL}" \
    --only-show-errors \
    "${SPIDER_RUN_DIR}/" \
    "${RUN_R2_PREFIX}/"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't sync to r2")
    exit 1
fi

RUN_END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
OUTPUT_FILESIZE=$(du -b "${SPIDER_RUN_DIR}/${RUN_GROUP}.zip" | awk '{ print $1 }')

# Create per-group latest.json
(>&2 echo "Creating per-group latest.json")

jq -n --compact-output \
    --arg run_id "${RUN_TIMESTAMP}" \
    --arg run_group "${RUN_GROUP}" \
    --arg run_output_url "${RUN_URL_PREFIX}/${RUN_GROUP}.zip" \
    --arg run_pmtiles_url "${RUN_URL_PREFIX}/${RUN_GROUP}.pmtiles" \
    --arg run_parquet_url "${RUN_URL_PREFIX}/${RUN_GROUP}.parquet" \
    --arg run_stats_url "${RUN_URL_PREFIX}/stats/_results.json" \
    --arg run_start_time "${RUN_START}" \
    --arg run_end_time "${RUN_END}" \
    --arg run_output_size "${OUTPUT_FILESIZE}" \
    --arg run_spider_count "${SPIDER_COUNT}" \
    --arg run_line_count "${OUTPUT_LINECOUNT}" \
    '{"run_id": $run_id, "group": $run_group, "output_url": $run_output_url, "pmtiles_url": $run_pmtiles_url, "parquet_url": $run_parquet_url, "stats_url": $run_stats_url, "start_time": $run_start_time, "end_time": $run_end_time, "size_bytes": $run_output_size | tonumber, "spiders": $run_spider_count | tonumber, "total_lines": $run_line_count | tonumber }' \
    > latest.json

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't create latest.json")
    exit 1
fi

# Upload per-group latest.json to S3 and R2
uv run aws s3 cp \
    --only-show-errors \
    latest.json \
    "s3://${S3_BUCKET}/runs/${RUN_GROUP}/latest.json"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't copy latest.json to S3")
    exit 1
fi

AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
uv run aws s3 \
    --endpoint-url="${R2_ENDPOINT_URL}" \
    cp \
    --only-show-errors \
    latest.json \
    "s3://${R2_BUCKET}/runs/${RUN_GROUP}/latest.json"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't copy latest.json to R2")
    exit 1
fi

(>&2 echo "Saved per-group latest.json")

# Create per-group history.json
(>&2 echo "Creating per-group history.json")

uv run aws s3 cp \
    --only-show-errors \
    "s3://${S3_BUCKET}/runs/${RUN_GROUP}/history.json" \
    history.json || true

if [ ! -s history.json ]; then
    echo '[]' > history.json
fi

jq --compact-output \
    --argjson latest_run_info "$(<latest.json)" \
    '. += [$latest_run_info]' history.json > history.json.tmp

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't append latest.json to history.json")
    exit 1
fi

mv history.json.tmp history.json

uv run aws s3 cp \
    --only-show-errors \
    history.json \
    "s3://${S3_BUCKET}/runs/${RUN_GROUP}/history.json"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't copy history.json to S3")
    exit 1
fi

AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
uv run aws s3 \
    --endpoint-url="${R2_ENDPOINT_URL}" \
    cp \
    --only-show-errors \
    history.json \
    "s3://${R2_BUCKET}/runs/${RUN_GROUP}/history.json"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't copy history.json to R2")
    exit 1
fi

(>&2 echo "Saved per-group history.json")

# Build group manifest
(>&2 echo "Building group manifest for ${RUN_GROUP}")

# Download previous manifest (if it exists)
uv run aws s3 cp \
    --only-show-errors \
    "s3://${S3_BUCKET}/runs/latest/${RUN_GROUP}.manifest.json" \
    "${SPIDER_RUN_DIR}/previous_manifest.json" || true

MANIFEST_ARGS=(
    --group "${RUN_GROUP}"
    --run-id "${RUN_TIMESTAMP}"
    --run-url-prefix "${RUN_URL_PREFIX}"
    --spider-list "${SPIDER_RUN_DIR}/spider_list.txt"
    --stats-dir "${SPIDER_RUN_DIR}/stats"
    --output "${SPIDER_RUN_DIR}/${RUN_GROUP}.manifest.json"
)

if [ -s "${SPIDER_RUN_DIR}/previous_manifest.json" ]; then
    MANIFEST_ARGS+=(--previous-manifest "${SPIDER_RUN_DIR}/previous_manifest.json")
fi

uv run python ci/build_group_manifest.py "${MANIFEST_ARGS[@]}"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't build group manifest")
    exit 1
fi

# Upload manifest to S3 and R2
uv run aws s3 cp \
    --only-show-errors \
    "${SPIDER_RUN_DIR}/${RUN_GROUP}.manifest.json" \
    "s3://${S3_BUCKET}/runs/latest/${RUN_GROUP}.manifest.json"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't upload manifest to S3")
    exit 1
fi

AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
uv run aws s3 \
    --endpoint-url="${R2_ENDPOINT_URL}" \
    cp \
    --only-show-errors \
    "${SPIDER_RUN_DIR}/${RUN_GROUP}.manifest.json" \
    "s3://${R2_BUCKET}/runs/latest/${RUN_GROUP}.manifest.json"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't upload manifest to R2")
    exit 1
fi

(>&2 echo "Uploaded group manifest")

# Invoke the assembler to combine all group manifests into the global latest
(>&2 echo "Invoking assembler")
ci/assemble_latest.sh

(>&2 echo "Group ${RUN_GROUP} run ${RUN_TIMESTAMP} complete")
