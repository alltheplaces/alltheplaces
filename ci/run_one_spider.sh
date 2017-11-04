#!/usr/bin/env bash

if [ ! $# == 1 ]; then
    (>&2 echo "Usage: $0 spider_name")
    exit
fi

if [ -f $S3_BUCKET ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

RUN_DIR=`mktemp -d` || exit 1
LOGFILE="${RUN_DIR}/log.txt"
OUTFILE="${RUN_DIR}/output.geojson"
SPIDER_NAME=$(basename $1)
SPIDER_NAME=${SPIDER_NAME%.py}
TIMESTAMP=$(date -u +%F-%H-%M-%S)
S3_KEY_PREFIX="results/${SPIDER_NAME}/${TIMESTAMP}"
S3_URL_PREFIX="s3://${S3_BUCKET}/${S3_KEY_PREFIX}"

scrapy runspider \
    -t geojson \
    -o "file://${OUTFILE}" \
    --loglevel=INFO \
    --logfile=$LOGFILE \
    $1

gzip < $LOGFILE > ${LOGFILE}.gz

aws s3 cp --quiet \
    --acl=public-read \
    --content-type "text/plain; charset=utf-8" \
    --content-encoding "gzip" \
    "${LOGFILE}.gz" \
    "${S3_URL_PREFIX}/log.txt"

if [ ! $? -eq 0 ]; then
    (>&2 echo "Couldn't save logfile to s3")
    exit 1
fi

if grep -q 'Stored geojson feed' $LOGFILE; then
    gzip < $OUTFILE > ${OUTFILE}.gz

    aws s3 cp --quiet \
        --acl=public-read \
        --content-type "application/json" \
        --content-encoding "gzip" \
        "${OUTFILE}.gz" \
        "${S3_URL_PREFIX}/output.geojson"

    if [ ! $? -eq 0 ]; then
        (>&2 echo "Couldn't save output to s3")
        exit 1
    fi
fi

echo "https://s3.amazonaws.com/${S3_BUCKET}/${S3_KEY_PREFIX}"

if grep -q spider_exceptions $LOGFILE; then
    exit 1
fi
