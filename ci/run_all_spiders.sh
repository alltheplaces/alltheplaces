#!/usr/bin/env bash
set -x
echo "git revision: ${GIT_COMMIT}"

if [ -z "${S3_BUCKET}" ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

if [ -z "${GITHUB_WORKSPACE}" ]; then
    (>&2 echo "Please set GITHUB_WORKSPACE environment variable")
    exit 1
fi

if [ -z "${GITHUB_TOKEN}" ]; then
    (>&2 echo "Please set GITHUB_TOKEN environment variable")
    exit 1
fi

GITHUB_AUTH="scraperbot:${GITHUB_TOKEN}"

RUN_START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
RUN_TIMESTAMP=$(date -u +%F-%H-%M-%S)
RUN_S3_KEY_PREFIX="runs/${RUN_TIMESTAMP}"
RUN_S3_PREFIX="s3://${S3_BUCKET}/${RUN_S3_KEY_PREFIX}"
RUN_URL_PREFIX="https://alltheplaces-data.openaddresses.io/${RUN_S3_KEY_PREFIX}"
SPIDER_RUN_DIR="${GITHUB_WORKSPACE}/output"
PARALLELISM=${PARALLELISM:-12}
SPIDER_TIMEOUT=${SPIDER_TIMEOUT:-28800} # default to 8 hours

mkdir -p "${SPIDER_RUN_DIR}"

(>&2 echo "Writing to ${SPIDER_RUN_DIR}")
(>&2 echo "Write out a file with scrapy commands to parallelize")
for spider in $(scrapy list -s REQUESTS_CACHE_ENABLED=False)
do
    echo "timeout -k 15s 8h scrapy crawl --output ${SPIDER_RUN_DIR}/output/${spider}.geojson:geojson --logfile ${SPIDER_RUN_DIR}/logs/${spider}.txt --loglevel ERROR --set TELNETCONSOLE_ENABLED=0 --set CLOSESPIDER_TIMEOUT=${SPIDER_TIMEOUT} --set LOGSTATS_FILE=${SPIDER_RUN_DIR}/stats/${spider}.json ${spider}" >> ${SPIDER_RUN_DIR}/commands.txt
done

mkdir -p "${SPIDER_RUN_DIR}/logs"
mkdir -p "${SPIDER_RUN_DIR}/stats"
mkdir -p "${SPIDER_RUN_DIR}/output"
SPIDER_COUNT=$(wc -l < "${SPIDER_RUN_DIR}/commands.txt" | tr -d ' ')

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

scrapy insights --atp-nsi-osm "${SPIDER_RUN_DIR}/output" --outfile "${SPIDER_RUN_DIR}/stats/_insights.json"
(>&2 echo "Done comparing against Name Suggestion Index and OpenStreetMap")

tippecanoe --cluster-distance=25 \
           --drop-rate=1 \
           --maximum-zoom=13 \
           --cluster-maxzoom=g \
           --layer="alltheplaces" \
           --read-parallel \
           --attribution="<a href=\"https://www.alltheplaces.xyz/\">All The Places</a> ${RUN_TIMESTAMP}" \
           -o "${SPIDER_RUN_DIR}/output.pmtiles" \
           "${SPIDER_RUN_DIR}"/output/*.geojson
retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't generate pmtiles")
    exit 1
fi
(>&2 echo "Done generating pmtiles")

(>&2 echo "Writing out summary JSON")
echo "{\"count\": ${SPIDER_COUNT}, \"results\": []}" >> "${SPIDER_RUN_DIR}/stats/_results.json"
for spider in $(scrapy list)
do
    spider_out_geojson="${SPIDER_RUN_DIR}/output/${spider}.geojson"
    spider_out_log="${SPIDER_RUN_DIR}/logs/${spider}.txt"
    statistics_json="${SPIDER_RUN_DIR}/stats/${spider}.json"

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

    spider_filename=$(scrapy spider_filename "${spider}")

    # use JQ to create an overall results JSON
    jq --compact-output \
        --arg spider_name "${spider}" \
        --arg spider_feature_count ${feature_count} \
        --arg spider_error_count ${error_count} \
        --arg spider_elapsed_time ${elapsed_time} \
        --arg spider_filename ${spider_filename} \
        '.results += [{"spider": $spider_name, "filename": $spider_filename, "errors": $spider_error_count | tonumber, "features": $spider_feature_count | tonumber, "elapsed_time": $spider_elapsed_time | tonumber}]' \
        "${SPIDER_RUN_DIR}/stats/_results.json" > "${SPIDER_RUN_DIR}/stats/_results.json.tmp"
    mv "${SPIDER_RUN_DIR}/stats/_results.json.tmp" "${SPIDER_RUN_DIR}/stats/_results.json"
done
(>&2 echo "Wrote out summary JSON")

(>&2 echo "Compressing output files")
(cd "${SPIDER_RUN_DIR}" && zip -r output.zip output)

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't zip output dir")
    exit 1
fi

(>&2 echo "Compressing log files")
(cd "${SPIDER_RUN_DIR}" && zip -r logs.zip logs)

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't zip logs dir")
    exit 1
fi

(>&2 echo "Saving log and output files to ${RUN_S3_PREFIX}")
aws s3 sync \
    --only-show-errors \
    "${SPIDER_RUN_DIR}/" \
    "${RUN_S3_PREFIX}/"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't sync to s3")
    exit 1
fi

(>&2 echo "Saving embed to https://data.alltheplaces.xyz/runs/latest/info_embed.html")
OUTPUT_FILESIZE=$(du -b "${SPIDER_RUN_DIR}/output.zip"  | awk '{ print $1 }')
OUTPUT_FILESIZE_PRETTY=$(echo "$OUTPUT_FILESIZE" | numfmt --to=si --format=%0.1f)
cat > "${SPIDER_RUN_DIR}/info_embed.html" << EOF
<html><body>
<a href="${RUN_URL_PREFIX}/output.zip">Download</a>
(${OUTPUT_FILESIZE_PRETTY})<br/><small>$(printf "%'d" "${OUTPUT_LINECOUNT}") rows from
${SPIDER_COUNT} spiders, updated $(date)</small>
</body></html>
EOF

aws s3 cp \
    --only-show-errors \
    --content-type "text/html; charset=utf-8" \
    "${SPIDER_RUN_DIR}/info_embed.html" \
    "s3://${S3_BUCKET}/runs/latest/info_embed.html"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't save info embed to s3")
    exit 1
fi

RUN_END=$(date -u +%Y-%m-%dT%H:%M:%SZ)

(>&2 echo "Creating latest.json")

jq -n --compact-output \
    --arg run_id "${RUN_TIMESTAMP}" \
    --arg run_output_url "${RUN_URL_PREFIX}/output.zip" \
    --arg run_pmtiles_url "${RUN_URL_PREFIX}/output.pmtiles" \
    --arg run_stats_url "${RUN_URL_PREFIX}/stats/_results.json" \
    --arg run_insights_url "${RUN_URL_PREFIX}/stats/_insights.json" \
    --arg run_start_time "${RUN_START}" \
    --arg run_end_time "${RUN_END}" \
    --arg run_output_size "${OUTPUT_FILESIZE}" \
    --arg run_spider_count "${SPIDER_COUNT}" \
    --arg run_line_count "${OUTPUT_LINECOUNT}" \
    '{"run_id": $run_id, "output_url": $run_output_url, "pmtiles_url": $run_pmtiles_url, "stats_url": $run_stats_url, "insights_url": $run_insights_url, "start_time": $run_start_time, "end_time": $run_end_time, "size_bytes": $run_output_size | tonumber, "spiders": $run_spider_count | tonumber, "total_lines": $run_line_count | tonumber }' \
    > latest.json

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't create latest.json")
    exit 1
fi

aws s3 cp \
    --only-show-errors \
    latest.json \
    "s3://${S3_BUCKET}/runs/latest.json"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't copy latest.json to S3")
    exit 1
fi

(>&2 echo "Saved latest.json to https://data.alltheplaces.xyz/runs/latest.json")

(>&2 echo "Creating history.json")

aws s3 cp \
    --only-show-errors \
    "s3://${S3_BUCKET}/runs/history.json" \
    history.json

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't copy history.json from S3")
    exit 1
fi

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

(>&2 echo "Saving history.json to https://data.alltheplaces.xyz/runs/history.json")

aws s3 cp \
    --only-show-errors \
    history.json \
    "s3://${S3_BUCKET}/runs/history.json"

retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "Couldn't copy history.json to S3")
    exit 1
fi

if [ -z "${BUNNY_API_KEY}" ]; then
    (>&2 echo "Skipping CDN cache purge because BUNNY_API_KEY environment variable not set")
else
    curl --request GET \
         --silent \
         --url 'https://api.bunny.net/purge?url=https%3A%2F%2Fdata.alltheplaces.xyz%2Fruns%2Flatest.json&async=false' \
         --header "AccessKey: ${BUNNY_API_KEY}" \
         --header 'accept: application/json'

    retval=$?
    if [ ! $retval -eq 0 ]; then
        (>&2 echo "Failed to purge latest.json from CDN")
        exit 1
    fi

    (>&2 echo "Purged latest.json from CDN")

    curl --request GET \
         --silent \
         --url 'https://api.bunny.net/purge?url=https%3A%2F%2Fdata.alltheplaces.xyz%2Fruns%2Fhistory.json&async=false' \
         --header "AccessKey: ${BUNNY_API_KEY}" \
         --header 'accept: application/json'

    retval=$?
    if [ ! $retval -eq 0 ]; then
        (>&2 echo "Failed to purge history.json from CDN")
        exit 1
    fi

    (>&2 echo "Purged history.json from CDN")
fi
