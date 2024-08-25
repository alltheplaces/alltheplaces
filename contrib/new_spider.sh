#!/usr/bin/env bash

echo "git checkout -b $1"
echo "touch locations/spiders/$1.py"
echo "git add locations/spiders/$1.py"
echo "black locations/spiders/$1.py"