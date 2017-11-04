#!/usr/bin/env bash

for spider in $(git diff --name-only HEAD..$TRAVIS_BRANCH | grep 'locations/spiders')
do
    output=$(./ci/run_one_spider.sh $spider)
    echo $output
done
