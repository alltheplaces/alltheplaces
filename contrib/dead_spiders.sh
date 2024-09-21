#!/usr/bin/env bash

echo '' > dead_spiders.txt
N=5
for RUN in $(curl https://data.alltheplaces.xyz/runs/history.json | jq -r ".[].stats_url" | tail -n $N); do
    curl $RUN | jq ".results" | jq ".[] | select(.features == 0) | .filename" >> dead_spiders.txt
done

# grep -w -f <(grep -w -o -e . dead_spiders.txt | sort | uniq -d) dead_spiders.txt
sort dead_spiders.txt | uniq -c | grep "$N " |  sed -E "s/      $N (.*)/\1/"
