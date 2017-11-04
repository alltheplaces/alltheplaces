#!/usr/bin/env bash

TMPFILE=$(mktemp)
RUN_TIMESTAMP=$(date -u +%s)
S3_PREFIX="s3://${S3_BUCKET}/runs/${RUN_TIMESTAMP}"

cat << _EOF_
<!DOCTYPE html>
<html>
<head>
</head>

<body>
<h1>Travis build ${TRAVIS_JOB_NUMBER}</h1>
<table>
<tr>
<th>
Spider
</th>
<th>
Results
</th>
<th>
Log
</th>
</tr>
_EOF_ >> $TMPFILE

for spider in $(git diff --name-only HEAD..$TRAVIS_BRANCH | grep 'locations/spiders')
do
    spider_url_root=$(./ci/run_one_spider.sh $spider)

    if [ ! $? -eq 0 ]; then
        (>&2 echo "Spider ${spider} failed")
    fi

    cat << _EOF_
    <tr>
    <td>
    <a href="https://github.com/${TRAVIS_REPO_SLUG}/blob/${TRAVIS_COMMIT}/${spider}"><code>${spider}</code></a>
    </td>
    <td>
    <a href="${spider_url_root}/output.geojson">GeoJSON</a>&nbsp;|&nbsp;
    <a href="http://placescraper-results.s3-website-us-east-1.amazonaws.com/map.html?show=${spider_url_root}/output.geojson">Map</a>
    </td>
    <td>
    <a href="${spider_url_root}/log.txt">Log</a>
    </td>
    </tr>
    _EOF_ >> $TMPFILE
done

cat << _EOF_
</table>
</body>
</html>
_EOF_ >> $TMPFILE

aws s3 cp --quiet \
    --acl=public-read \
    --content-type "text/html" \
    $TMPFILE \
    $S3_PREFIX.html
