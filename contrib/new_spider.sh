#!/usr/bin/env bash

echo "git fetch upstream && git checkout upstream/master && git checkout -b $1 && pipenv run scrapy genspider -t basic -d $1 > locations/spiders/$1.py && git add locations/spiders/$1.py && code locations/spiders/$1.py"
echo "pipenv run scrapy crawl $1 && bash contrib/hooks/pre-commit && git commit -m 'Add $1' locations/spiders/$1.py && git push -u origin $1"

