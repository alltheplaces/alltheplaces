#!/usr/bin/env bash

BUILD_ID=$1

if [ -z "${BUILD_ID}" ]; then
    (>&2 echo "Missing BUILD_ID")
    (>&2 echo "Try '$0 2022-10-08-13-31-39'")
    exit 1
fi

mkdir -p "${BUILD_ID}"

SPIDERS=$(curl "https://data.alltheplaces.xyz/runs/${BUILD_ID}/stats/_results.json" | jq -r ".results[].spider")
for SPIDER in $SPIDERS
do
  curl "https://data.alltheplaces.xyz/runs/${BUILD_ID}/stats/${SPIDER}.json" -o "${BUILD_ID}/${SPIDER}.json"
done
