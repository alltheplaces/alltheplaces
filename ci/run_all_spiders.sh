#!/usr/bin/env bash

if [ -f $S3_BUCKET ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

RUN_START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
RUN_TIMESTAMP=$(date -u +%F-%H-%M-%S)
RUN_S3_KEY_PREFIX="runs/${RUN_TIMESTAMP}"
RUN_S3_PREFIX="s3://${S3_BUCKET}/${RUN_S3_KEY_PREFIX}"
RUN_URL_PREFIX="https://s3.amazonaws.com/${S3_BUCKET}/${RUN_S3_KEY_PREFIX}"
SPIDER_RUN_DIR=`mktemp -d` || exit 1
PARALLELISM=${PARALLELISM:-12}
SPIDER_TIMEOUT=${SPIDER_TIMEOUT:-14400} # default to 4 hours

(>&2 echo "Writing to ${SPIDER_RUN_DIR}")
(>&2 echo "Write out a file with scrapy commands to parallelize")
for spider in $(scrapy list)
do
    echo "--output ${SPIDER_RUN_DIR}/output/${spider}.geojson --output-format geojson --logfile ${SPIDER_RUN_DIR}/logs/${spider}.log --loglevel ERROR --set TELNETCONSOLE_ENABLED=0 --set CLOSESPIDER_TIMEOUT=${SPIDER_TIMEOUT} ${spider}" >> ${SPIDER_RUN_DIR}/commands.txt
done

mkdir -p ${SPIDER_RUN_DIR}/logs
mkdir -p ${SPIDER_RUN_DIR}/output
SPIDER_COUNT=$(wc -l < ${SPIDER_RUN_DIR}/commands.txt | tr -d ' ')

(>&2 echo "Running ${SPIDER_COUNT} spiders ${PARALLELISM} at a time")
xargs -t -L 1 -P ${PARALLELISM} scrapy crawl < ${SPIDER_RUN_DIR}/commands.txt

if [ ! $? -eq 0 ]; then
    (>&2 echo "Xargs failed with exit code ${?}")
    exit 1
fi
(>&2 echo "Done running spiders")

OUTPUT_LINECOUNT=$(cat ${SPIDER_RUN_DIR}/output/*.geojson | wc -l | tr -d ' ')
(>&2 echo "Generated ${OUTPUT_LINECOUNT} lines")

echo "{\"count\": ${SPIDER_COUNT}, \"results\": []}" >> ${SPIDER_RUN_DIR}/output/results.json
for spider in $(scrapy list)
do
    spider_out_geojson="${SPIDER_RUN_DIR}/output/${spider}.geojson"
    spider_out_log="${SPIDER_RUN_DIR}/logs/${spider}.log"
    cat ${SPIDER_RUN_DIR}/output/results.json | \
        jq --compact-output \
            --arg spider_name ${spider} \
            --arg spider_feature_count $(wc -l < ${spider_out_geojson}) \
            --arg spider_error_count $(grep ' ERROR: ' ${spider_out_log} | wc -l | tr -d ' ') \
            '.results += [{"spider": $spider_name, "errors": $spider_error_count | tonumber, "features": $spider_feature_count | tonumber}]' \
        > ${SPIDER_RUN_DIR}/output/results.json
done
(>&2 echo "Wrote out summary JSON")

(>&2 echo "Concatenating and compressing output files")
tar -czf ${SPIDER_RUN_DIR}/output.tar.gz -C ${SPIDER_RUN_DIR} ./output

(>&2 echo "Concatenating and compressing log files")
tar -czf ${SPIDER_RUN_DIR}/logs.tar.gz -C ${SPIDER_RUN_DIR} ./logs

(>&2 echo "Saving log and output files to ${RUN_URL_PREFIX}")
aws s3 sync \
    --only-show-errors \
    --acl=public-read \
    "${SPIDER_RUN_DIR}/" \
    "${RUN_S3_PREFIX}/"

if [ ! $? -eq 0 ]; then
    (>&2 echo "Couldn't sync to s3")
    exit 1
fi

(>&2 echo "Updating runs.json with new runs")
RUN_FINISH=$(date -u +%Y-%m-%dT%H:%M:%SZ)
aws s3 cp \
    --only-show-errors \
    "s3://${S3_BUCKET}/runs.json" \
    "runs.json"
cat runs.json | \
    jq \
        --compact-output \
        --arg run_start $RUN_START \
        --arg run_finish $RUN_FINISH \
        --arg run_name $RUN_TIMESTAMP \
        --arg spider_count $SPIDER_COUNT \
        --arg feature_count $OUTPUT_LINECOUNT \
        '.runs += [{"start": $run_start, "finish": $run_finish, "name": $run_name, "spider_count": $spider_count | tonumber, "feature_count": $feature_count | tonumber}]' \
    > runs.json
aws s3 cp \
    --only-show-errors \
    --acl=public-read \
    "runs.json" \
    "s3://${S3_BUCKET}/runs.json"
(>&2 echo "Saved updated runs.json to https://s3.amazonaws.com/${S3_BUCKET}/runsjson")

(>&2 echo "Saving embed to https://s3.amazonaws.com/${S3_BUCKET}/runs/latest/info_embed.html")
OUTPUT_FILESIZE=$(du ${SPIDER_RUN_DIR}/output.tar.gz | awk '{printf "%0.1f", $1/1024}')
cat > "${SPIDER_RUN_DIR}/info_embed.html" << EOF
<html><body>
<a href="${RUN_URL_PREFIX}/output.tar.gz">Download</a>
(${OUTPUT_FILESIZE} MB)<br/><small>$(printf "%'d" ${OUTPUT_LINECOUNT}) rows from
${SPIDER_COUNT} spiders, updated $(date)</small>
</body></html>
EOF

aws s3 cp \
    --only-show-errors \
    --acl=public-read \
    --content-type "text/html; charset=utf-8" \
    "${SPIDER_RUN_DIR}/info_embed.html" \
    "s3://${S3_BUCKET}/runs/latest/info_embed.html"

if [ ! $? -eq 0 ]; then
    (>&2 echo "Couldn't save info embed to s3")
    exit 1
fi
