#!/usr/bin/env bash

if [ -z "${EDITOR}" ]; then 
if command -v code &> /dev/null
then
    EDITOR='code'
elif command -v nano &> /dev/null
    EDITOR='nano'
fi

echo "Generate your new spider. Tip: Do this a new terminal"
echo "git fetch upstream && git checkout upstream/master && git checkout -b $1 && pipenv run scrapy genspider $1 $1 && git add locations/spiders/$1.py && $EDITOR locations/spiders/$1.py"

echo ""
echo "Crawl and commit"
echo "pipenv run scrapy crawl $1 && bash contrib/hooks/pre-commit && git commit -m 'Add $1' locations/spiders/$1.py && git push -u origin $1"

