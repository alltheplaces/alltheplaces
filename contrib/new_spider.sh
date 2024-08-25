#!/usr/bin/env bash

echo "git fetch upstream"
echo "git checkout upstream/master"
echo "git checkout -b $1"
echo "touch locations/spiders/$1.py"
echo "git add locations/spiders/$1.py"
echo "pipenv run scrapy crawl $1"
echo "bash .git/hooks/pre-commit"
echo "git commit -m 'Add $1' locations/spiders/$1.py"
echo "git push -u origin $1"

