#!/usr/bin/env bash

if [ ! $# == 1 ]; then
    (>&2 echo "Usage: $0 spider_name")
    exit
fi

RUN_DIR=`mktemp -d` || exit 1
LOGFILE="${RUN_DIR}/log.txt"
OUTFILE="${RUN_DIR}/output.geojson"
SPIDER_NAME=$(basename $1)
SPIDER_NAME=${SPIDER_NAME%.py}

scrapy runspider \
    -t geojson \
    -o "file://${OUTFILE}" \
    --loglevel=INFO \
    --logfile=$LOGFILE \
    $1

echo $RUN_DIR

if grep -q spider_exceptions $LOGFILE; then
    exit 1
fi
