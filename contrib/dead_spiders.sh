#!/usr/bin/env bash

echo '' > dead_spiders.txt
# Number of builds to check
N=5
curl -s https://data.alltheplaces.xyz/runs/history.json > history.json

for RUN in $(cat history.json | jq -r ".[].stats_url" | tail -n $N); do
    curl -s $RUN | jq ".results" | jq ".[] | select(.features == 0) | .filename" >> dead_spiders.txt
    echo "Fetched $RUN"
done

# Most recent build
BUILD_ID=$(cat history.json | jq -r ".[-1].run_id")

# Detect where there are N duplicates, indicating no output for all N runs
FILES=$(sort dead_spiders.txt | uniq -c | grep "$N " |  sed -E "s/      $N (.*)/\1/")

for FILE in $FILES; do
    PR_NAME=$(echo $FILE |  sed -E "s/\"locations\/spiders\/(.*)\.py\"/\1/")

    # Ensure we have the stats for the latest build for this spider
    if [ ! -f "${BUILD_ID}/${PR_NAME}.json" ]; then
        echo "Gathering stats for https://data.alltheplaces.xyz/runs/${BUILD_ID}/stats/${PR_NAME}.json to ${BUILD_ID}/${PR_NAME}.json" 
        curl -s "https://data.alltheplaces.xyz/runs/${BUILD_ID}/stats/${PR_NAME}.json" | jq > "${BUILD_ID}/${PR_NAME}.json"
    fi

    # Check the stats
    # Cloudflare or akamai 403? Requires proxy perhaps
    # HTTP 500? DNS failure? Dead

    NUM_ERRORS=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["log_count/ERROR"]')))
    if [ $NUM_ERRORS -ge 1 ]; then
        echo "Spider $PR_NAME finished with $NUM_ERRORS errors - remove?"
        echo "git checkout upstream/master && git checkout -b $PR_NAME && git rm $FILE && git commit -m 'Remove dead spider' $FILE && git push -u origin $PR_NAME" 
        echo ""
    fi
done