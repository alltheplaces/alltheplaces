#!/usr/bin/env bash

if [ -f $S3_BUCKET ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

TMPFILE=$(mktemp)
RUN_TIMESTAMP=$(date -u +%s)
S3_PREFIX="s3://${S3_BUCKET}/runs/${RUN_TIMESTAMP}"

cat << EOF >> $TMPFILE
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
EOF

case "$TRAVIS_EVENT_TYPE" in
    "cron")
        SPIDERS=$(find locations/spiders -type f -name "[a-z][a-z_]*.py")
        ;;
    "push" | "pull_request")
        SPIDERS=$(git diff --name-only HEAD..$TRAVIS_BRANCH | grep 'locations/spiders')
        ;;
    *)
        echo "Unknown event type ${TRAVIS_EVENT_TYPE}"
        exit 1
        ;;
esac

for spider in $SPIDERS
do
    (>&2 echo "Running spider at ${spider}")
    SPIDER_RUN_DIR=$(./ci/run_one_spider.sh $spider)

    if [ ! $? -eq 0 ]; then
        (>&2 echo "Spider ${spider} failed")
    fi

    LOGFILE="${SPIDER_RUN_DIR}/log.txt"
    OUTFILE="${SPIDER_RUN_DIR}/output.geojson"
    TIMESTAMP=$(date -u +%F-%H-%M-%S)
    S3_KEY_PREFIX="results/${SPIDER_NAME}/${TIMESTAMP}"
    S3_URL_PREFIX="s3://${S3_BUCKET}/${S3_KEY_PREFIX}"

    gzip < $LOGFILE > ${LOGFILE}.gz

    aws s3 cp --quiet \
        --acl=public-read \
        --content-type "text/plain; charset=utf-8" \
        --content-encoding "gzip" \
        "${LOGFILE}.gz" \
        "${S3_URL_PREFIX}/log.txt"

    if [ ! $? -eq 0 ]; then
        (>&2 echo "Couldn't save logfile to s3")
        exit 1
    fi

    if grep -q 'Stored geojson feed' $LOGFILE; then
        gzip < $OUTFILE > ${OUTFILE}.gz

        aws s3 cp --quiet \
            --acl=public-read \
            --content-type "application/json" \
            --content-encoding "gzip" \
            "${OUTFILE}.gz" \
            "${S3_URL_PREFIX}/output.geojson"

        if [ ! $? -eq 0 ]; then
            (>&2 echo "Couldn't save output to s3")
            exit 1
        fi
    fi

    cat << EOF >> $TMPFILE
    <tr>
        <td>
        <a href="https://github.com/${TRAVIS_REPO_SLUG}/blob/${TRAVIS_COMMIT}/${spider}"><code>${spider}</code></a>
        </td>
        <td>
        <a href="${spider_url_root}/output.geojson">$(wc -l < ${OUTFILE} | tr -d ' ') results</a>
        (<a href="https://s3.amazonaws.com/${S3_BUCKET}/map.html?show=${spider_url_root}/output.geojson">Map</a>)
        </td>
        <td>
        <a href="${spider_url_root}/log.txt">Log</a>
        </td>
    </tr>
EOF
done

cat << EOF >> $TMPFILE
</table>
</body>
</html>
EOF

aws s3 cp --quiet \
    --acl=public-read \
    --content-type "text/html" \
    ${TMPFILE} \
    "${S3_PREFIX}.html"
