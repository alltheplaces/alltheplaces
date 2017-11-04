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
S3_PREFIX="s3://${S3_BUCKET}/results/${SPIDER_NAME}/${TIMESTAMP}"

scrapy runspider \
    -t geojson \
    -o "file://${OUTFILE}" \
    --loglevel=DEBUG \
    --logfile=$LOGFILE \
    $1

aws s3 cp --quiet --acl=public-read \
    $LOGFILE \
    $S3_PREFIX/log.txt

if [ ! $? -eq 0 ]; then
    (>&2 echo "Couldn't save logfile to s3")
    exit 1
fi

if grep -q 'Stored geojson feed' $LOGFILE; then
    aws s3 cp --quiet --acl=public-read \
        $OUTFILE \
        $S3_PREFIX/output.geojson

    if [ ! $? -eq 0 ]; then
        (>&2 echo "Couldn't save output to s3")
        exit 1
    fi
fi

echo $S3_PREFIX

if grep -q spider_exceptions $LOGFILE; then
    exit 1
fi
