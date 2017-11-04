#!/usr/bin/env bash

for i in $(git diff --name-only HEAD..$TRAVIS_BRANCH | grep 'locations/spiders')
do
    echo $i
done
