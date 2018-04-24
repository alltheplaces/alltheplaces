#!/usr/bin/env bash

if [ -f $S3_BUCKET ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

RUN_TIMESTAMP=$(date -u +%F-%H-%M-%S)
RUN_S3_KEY_PREFIX="runs/${RUN_TIMESTAMP}"
RUN_S3_PREFIX="s3://${S3_BUCKET}/${RUN_S3_KEY_PREFIX}"
RUN_URL_PREFIX="https://s3.amazonaws.com/${S3_BUCKET}/${RUN_S3_KEY_PREFIX}"
SPIDER_RUN_DIR=`mktemp -d` || exit 1
PARALLELISM=${PARALLELISM:-12}
SPIDER_TIMEOUT=${SPIDER_TIMEOUT:-14400} # default to 4 hours

(>&2 echo "Tmp is ${SPIDER_RUN_DIR}")
(>&2 echo "Write out a file with scrapy commands to parallelize")
for spider in $(scrapy list)
do
    echo "--output ${SPIDER_RUN_DIR}/${spider}.geojson --output-format geojson --logfile ${SPIDER_RUN_DIR}/logs/${spider}.log --loglevel INFO --set TELNETCONSOLE_ENABLED=0 --set CLOSESPIDER_TIMEOUT=${SPIDER_TIMEOUT} ${spider}" >> ${SPIDER_RUN_DIR}/commands.txt
done

mkdir -p ${SPIDER_RUN_DIR}/logs
SPIDER_COUNT=$(wc -l < ${SPIDER_RUN_DIR}/commands.txt | tr -d ' ')

(>&2 echo "Running ${SPIDER_COUNT} spiders ${PARALLELISM} at a time")
xargs -t -L 1 -P ${PARALLELISM} scrapy crawl < ${SPIDER_RUN_DIR}/commands.txt

if [ ! $? -eq 0 ]; then
    (>&2 echo "Xargs failed with exit code ${?}")
    exit 1
fi
(>&2 echo "Done running spiders")

(>&2 echo "Concatenating and compressing output files")
cat ${SPIDER_RUN_DIR}/*.geojson > ${SPIDER_RUN_DIR}/output.geojson
gzip < ${SPIDER_RUN_DIR}/output.geojson > ${SPIDER_RUN_DIR}/output.geojson.gz
OUTPUT_LINECOUNT=$(wc -l < ${SPIDER_RUN_DIR}/output.geojson | tr -d ' ')
(>&2 echo "Generated ${OUTPUT_LINECOUNT} lines")
OUTPUT_FILESIZE=$(du ${SPIDER_RUN_DIR}/output.geojson.gz | awk '{printf "%0.1f", $1/1024}')

(>&2 echo "Compressing log files")
tar -czf ${SPIDER_RUN_DIR}/logs.tar.gz -C ${SPIDER_RUN_DIR} ./logs

(>&2 echo "Saving log files to ${RUN_URL_PREFIX}/logs.tar.gz")
aws s3 cp --only-show-errors \
    --acl=public-read \
    --content-type "application/gzip" \
    "${SPIDER_RUN_DIR}/logs.tar.gz" \
    "${RUN_S3_PREFIX}/logs.tar.gz"

if [ ! $? -eq 0 ]; then
    (>&2 echo "Couldn't save logfiles to s3")
    exit 1
fi

(>&2 echo "Saving output to ${RUN_URL_PREFIX}/output.geojson.gz")
aws s3 cp --only-show-errors \
    --acl=public-read \
    --content-type "application/gzip" \
    "${SPIDER_RUN_DIR}/output.geojson.gz" \
    "${RUN_S3_PREFIX}/output.geojson.gz"

if [ ! $? -eq 0 ]; then
    (>&2 echo "Couldn't save output to s3")
    exit 1
fi

(>&2 echo "Saving embed to https://s3.amazonaws.com/${S3_BUCKET}/runs/latest/info_embed.html")
cat > "${SPIDER_RUN_DIR}/info_embed.html" << EOF
<html><body>
<a href="${RUN_URL_PREFIX}/output.geojson.gz">Download</a>
(${OUTPUT_FILESIZE} MB)<br/><small>$(printf "%'d" ${OUTPUT_LINECOUNT}) rows from
${SPIDER_COUNT} spiders, updated $(date)</small>
</body></html>
EOF

aws s3 cp --only-show-errors \
    --acl=public-read \
    --content-type "text/html; charset=utf-8" \
    "${SPIDER_RUN_DIR}/info_embed.html" \
    "s3://${S3_BUCKET}/runs/latest/info_embed.html"

if [ ! $? -eq 0 ]; then
    (>&2 echo "Couldn't save info embed to s3")
    exit 1
fi
