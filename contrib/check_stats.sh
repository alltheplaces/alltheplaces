#!/usr/bin/env bash

BUILD_ID=$1
STAT=$2

if [ -z "${BUILD_ID}" ]; then
    (>&2 echo "Missing BUILD_ID")
    (>&2 echo "Try '$0 2022-10-08-13-31-39 atp/nsi/match_perfect'")
    exit 1
fi

if [ -z "${STAT}" ]; then
    (>&2 echo "Missing STAT")
    (>&2 echo "Try '$0 2022-10-08-13-31-39 atp/nsi/match_perfect'")
    exit 1
fi

if [ ! -d "${BUILD_ID}" ]; then
    (>&2 echo "Missing data")
    (>&2 echo "Try './fetch_all_stats.sh 2022-10-08-13-31-39'")
    exit 1
fi

ITEM_COUNT=0
SPIDER_COUNT=0
for SPIDER in "$BUILD_ID"/*.json; do
    COUNT=$(cat $SPIDER | jq -r '."'"$STAT"'" // empty')
    if [[ ! -z "$COUNT" ]]; then
        echo "$SPIDER: $COUNT"
        ITEM_COUNT=$(($ITEM_COUNT + $COUNT))
        SPIDER_COUNT=$(($SPIDER_COUNT + 1))
    fi
done

echo "Spider Count: $SPIDER_COUNT"
echo "Item Count: $ITEM_COUNT"
