#!/usr/bin/env bash

if [ -f $S3_BUCKET ]; then
    (>&2 echo "Please set S3_BUCKET environment variable")
    exit 1
fi

TMPFILE=$(mktemp)
RUN_TIMESTAMP=$(date -u +%s)
RUN_S3_KEY_PREFIX="runs/${RUN_TIMESTAMP}"
RUN_S3_PREFIX="s3://${S3_BUCKET}/${RUN_S3_KEY_PREFIX}"
RUN_URL_PREFIX="https://s3.amazonaws.com/${S3_BUCKET}/${RUN_S3_KEY_PREFIX}"
PR_COMMENT_BODY="I ran the spiders in this pull request and got these results:\\n\\n|Spider|Results|Log|\\n|---|---|---|\\n"

case "$TRAVIS_EVENT_TYPE" in
    "cron" | "api")
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

FAIL_THE_BUILD=0
for spider in $SPIDERS
do
    (>&2 echo "${spider} running ...")
    SPIDER_RUN_DIR=`mktemp -d` || exit 1
    LOGFILE="${SPIDER_RUN_DIR}/log.txt"
    OUTFILE="${SPIDER_RUN_DIR}/output.geojson"

    scrapy runspider \
        -t geojson \
        -o "file://${OUTFILE}" \
        --loglevel=INFO \
        --logfile=$LOGFILE \
        -s CLOSESPIDER_TIMEOUT=60 \
        -s CLOSESPIDER_ERRORCOUNT=1 \
        $spider

    FAILURE_REASON="success"
    if grep -q "Spider closed (closespider_errorcount)" $LOGFILE; then
        (>&2 echo "${spider} exited with errors")
        FAIL_THE_BUILD=1
        FAILURE_REASON="exception"
    elif grep -q "Spider closed (closespider_timeout)" $LOGFILE; then
        (>&2 echo "${spider} exited because of timeout")
        FAILURE_REASON="timeout"
    fi

    TIMESTAMP=$(date -u +%F-%H-%M-%S)
    SPIDER_NAME=$(basename $spider)
    SPIDER_NAME=${SPIDER_NAME%.py}
    S3_KEY_PREFIX="results/${SPIDER_NAME}/${TIMESTAMP}"
    S3_URL_PREFIX="s3://${S3_BUCKET}/${S3_KEY_PREFIX}"
    HTTP_URL_PREFIX="https://s3.amazonaws.com/${S3_BUCKET}/${S3_KEY_PREFIX}"

    gzip < $LOGFILE > ${LOGFILE}.gz

    aws s3 cp --quiet \
        --acl=public-read \
        --content-type "text/plain; charset=utf-8" \
        --content-encoding "gzip" \
        "${LOGFILE}.gz" \
        "${S3_URL_PREFIX}/log.txt"

    if [ ! $? -eq 0 ]; then
        (>&2 echo "${spider} couldn't save logfile to s3")
        FAIL_THE_BUILD=1
    fi

    (>&2 echo "${spider} logfile is: ${S3_URL_PREFIX}/log.txt")

    FEATURE_COUNT=$(wc -l < ${OUTFILE} | tr -d ' ')

    if grep -q 'Stored geojson feed' $LOGFILE; then
        gzip < $OUTFILE > ${OUTFILE}.gz

        echo "${spider} has ${FEATURE_COUNT} features"

        aws s3 cp --quiet \
            --acl=public-read \
            --content-type "application/json" \
            --content-encoding "gzip" \
            "${OUTFILE}.gz" \
            "${S3_URL_PREFIX}/output.geojson"

        if [ ! $? -eq 0 ]; then
            (>&2 echo "${spider} couldn't save output to s3")
            FAIL_THE_BUILD=1
        fi

        (>&2 echo "${spider} output is: ${S3_URL_PREFIX}/output.geojson")
    fi

    PR_COMMENT_BODY="${PR_COMMENT_BODY}|[\`$spider\`](https://github.com/${TRAVIS_REPO_SLUG}/blob/${TRAVIS_COMMIT}/${spider})|[${FEATURE_COUNT} items](${HTTP_URL_PREFIX}/output.geojson) ([Map](https://s3.amazonaws.com/${S3_BUCKET}/map.html?show=${HTTP_URL_PREFIX}/output.geojson))|Resulted in a \`${FAILURE_REASON}\` ([Log](${HTTP_URL_PREFIX}/log.txt))|\\n"

    (>&2 echo "${spider} done")
done

if [ -z "$SPIDERS" ]; then
    echo "No spiders run"
    exit 0
fi

if [ -z "$GITHUB_TOKEN" ]; then
    echo "No GITHUB_TOKEN set"
else
    if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
        curl \
            -s \
            -XPOST \
            -H "Authorization: token ${GITHUB_TOKEN}" \
            -d "{\"body\":\"${PR_COMMENT_BODY}\"}" \
            "https://api.github.com/repos/${TRAVIS_REPO_SLUG}/issues/${TRAVIS_PULL_REQUEST}/comments"
        echo "Added a comment to pull https://github.com/${TRAVIS_REPO_SLUG}/pull/${TRAVIS_PULL_REQUEST}"
    else
        echo "Not posting to GitHub because no pull TRAVIS_PULL_REQUEST set"
    fi
fi

exit $FAIL_THE_BUILD
