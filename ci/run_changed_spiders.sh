#!/usr/bin/env bash

for spider in $(git diff --name-only HEAD..$TRAVIS_BRANCH | grep 'locations/spiders')
do
    output=$(./ci/run_one_spider.sh $spider)

    if [ ! $? -eq 0 ]; then
        (>&2 echo "Spider ${spider} failed")
        exit 1
    fi

    echo $output
done
