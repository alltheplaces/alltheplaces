#!/usr/bin/env bash

echo $(pwd)
for spider in $(git diff --name-only HEAD..$TRAVIS_BRANCH | grep 'locations/spiders')
do
    output=$(./run_one_spider.sh $spider)
    echo $output
done
