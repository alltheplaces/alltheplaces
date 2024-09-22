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

    NUM_AKAMAI_BAD_REQUEST=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["atp/cdn/akamai/response_status_count/400"]')))
    NUM_AKAMAI_FORBIDDEN=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["atp/cdn/akamai/response_status_count/403"]')))
    NUM_CLOUDFLARE_FORBIDDEN=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["/cdn/cloudflare/response_status_count/403"]')))
    NUM_ERRORS=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["log_count/ERROR"]')))
    NUM_OFFSITE=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["offsite/filtered"]')))

    NUM_HTTP_ERRORS=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["httperror/response_ignored_status_count"]')))
    NUM_404_ERRORS=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["httperror/response_ignored_status_count/404"]')))
    NUM_400_ERRORS=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["httperror/response_ignored_status_count/400"]')))
    NUM_403_ERRORS=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["httperror/response_ignored_status_count/403"]')))

    NUM_301_ERRORS=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["downloader/response_status_count/301"]')))
    NUM_307_ERRORS=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["downloader/response_status_count/307"]')))
    NUM_308_ERRORS=$(($(cat "${BUILD_ID}/${PR_NAME}.json" | jq '.["downloader/response_status_count/308"]')))



    if [ $NUM_AKAMAI_FORBIDDEN -ge 1 ] || [ $NUM_AKAMAI_BAD_REQUEST -ge 1 ]; then
        echo "Spider $PR_NAME finished with $NUM_AKAMAI_FORBIDDEN forbidden, $NUM_AKAMAI_BAD_REQUEST - flag as requires proxy?"
    elif [ $NUM_CLOUDFLARE_FORBIDDEN -ge 1 ]; then
        echo "Spider $PR_NAME finished with $NUM_CLOUDFLARE_FORBIDDEN forbidden - flag as requires proxy??"
    elif [ $NUM_OFFSITE -ge 1 ]; then
        echo "Spider $PR_NAME finished with a $NUM_OFFSITE offsite requests - domain changed?"
    elif [ $NUM_HTTP_ERRORS -ge 1 ] || [ $NUM_400_ERRORS -ge 1 ] || [ $NUM_404_ERRORS -ge 1 ] || [ $NUM_403_ERRORS -ge 1 ]; then
        echo "git checkout upstream/master && git branch -D $PR_NAME ; git checkout -b $PR_NAME && git rm $FILE && git commit -m 'Remove dead spider: $PR_NAME finished with a $NUM_HTTP_ERRORS HTTP errors (400: $NUM_400_ERRORS, 404: $NUM_404_ERRORS, 403: $NUM_403_ERRORS) - remove?' $FILE && git push --force -u origin $PR_NAME" 
    elif [ $NUM_301_ERRORS -ge 1 ] || [ $NUM_307_ERRORS -ge 1 ] || [ $NUM_308_ERRORS -ge 1 ]; then
        echo "git checkout upstream/master && git branch -D $PR_NAME ; git checkout -b $PR_NAME && git rm $FILE && git commit -m 'Remove dead spider: $PR_NAME finished with $NUM_301_ERRORS 301 redirects, $NUM_307_ERRORS 307 redirects, $NUM_308_ERRORS 308 redirects' $FILE && git push --force -u origin $PR_NAME" 
    elif [ $NUM_ERRORS -ge 1 ]; then
        if [ curl -s https://alltheplaces-data.openaddresses.io/runs/$BUILD_ID/logs/$PR_NAME.txt | grep -q DNSLookupError ]; then
            echo "git checkout upstream/master && git branch -D $PR_NAME ; git checkout -b $PR_NAME && git rm $FILE && git commit -m 'Remove dead spider: $PR_NAME has DNS Lookup Issues' $FILE && git push --force -u origin $PR_NAME" 
        else
            echo "$BROWSER \"https://github.com/alltheplaces/alltheplaces/issues/new?title=$PR_NAME+broken&body=https://alltheplaces-data.openaddresses.io/runs/$BUILD_ID/logs/$PR_NAME.txt\""
        fi
    else
        echo "Spider $PR_NAME broken silently"
        # echo "$BROWSER \"https://github.com/alltheplaces/alltheplaces/issues/new?title=$PR_NAME+broken&body=https://alltheplaces-data.openaddresses.io/runs/$BUILD_ID/logs/$PR_NAME.txt\'"
        # echo "git checkout upstream/master && git branch -D $PR_NAME ; git checkout -b $PR_NAME && git rm $FILE && git commit -m 'Remove dead spider' $FILE && git push --force -u origin $PR_NAME" 

    fi
done