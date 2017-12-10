#!/usr/bin/env bash

if [ -f $S3_BUCKET ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

RUN_TIMESTAMP=$(date -u +%s)
RUN_S3_KEY_PREFIX="runs/${RUN_TIMESTAMP}"
RUN_S3_PREFIX="s3://${S3_BUCKET}/${RUN_S3_KEY_PREFIX}"
RUN_URL_PREFIX="https://s3.amazonaws.com/${S3_BUCKET}/${RUN_S3_KEY_PREFIX}"

(>&2 echo "Running all spiders")

python "ci/run_all_spiders.py"

if [ ! $? -eq 0 ]; then
    (>&2 echo "Running spiders failed for some reason")
    exit 1
fi

(>&2 echo "Gzipping output")

gzip all_spiders.log
gzip output.ndgeojson

(>&2 echo "Copying results to S3")

aws s3 cp --quiet \
    --acl=public-read \
    --content-type "application/json" \
    --content-encoding "gzip" \
    "output.ndgeojson.gz" \
    "${RUN_S3_PREFIX}/output.ndgeojson.gz"

aws s3 cp --quiet \
    --acl=public-read \
    --content-type "text/plain; charset=utf-8" \
    --content-encoding "gzip" \
    "all_spiders.log.gz" \
    "${RUN_S3_PREFIX}/all_spiders.log.gz"

(>&2 echo "Done")
