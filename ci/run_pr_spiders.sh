#!/bin/bash
PR_COMMENT_BODY="I ran the spiders in this pull request and got these results:\\n\\n|Spider|Results|Log|\\n|---|---|---|\\n"

# Check if the build is triggered by a pull request
if [ "${CODEBUILD_WEBHOOK_EVENT}" = "PULL_REQUEST_CREATED" ] || [ "${CODEBUILD_WEBHOOK_EVENT}" = "PULL_REQUEST_UPDATED" ]; then          # Extract the pull request number from the CODEBUILD_SOURCE_VERSION variable
  # CODEBUILD_SOURCE_VERSION format: "pr/pull-request-number"
  pull_request_number=$(echo "${CODEBUILD_SOURCE_VERSION}" | cut -d '/' -f 2)

  echo "Pull request number: ${pull_request_number}"
else
  echo "This build is not triggered by a pull request. It was ${CODEBUILD_WEBHOOK_EVENT}"
  exit 1
fi

# If the most recent commit on the PR is from the pre-commit bot, skip running the spiders
if git log -1 --pretty=format:%an | grep -q "pre-commit"; then
  echo "Skipping spider run for pre-commit changes."
  exit 0
fi

pr_file_changes=$(curl -sL --header "authorization: Bearer ${GITHUB_TOKEN}" "https://api.github.com/repos/alltheplaces/alltheplaces/pulls/${pull_request_number}/files")
(>&2 echo "PR response: ${pr_file_changes}")

SPIDERS=$(echo "${pr_file_changes}" | jq -r '.[] | select(.status != "removed") | select(.filename | startswith("locations/spiders/")) | .filename')
retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "checking file changes failed. response was ${pr_file_changes}")
    exit 1
fi

spider_count=$(echo -n "${pr_file_changes}" | jq -r '[.[] | select(.status != "removed") | select(.filename | startswith("locations/spiders/"))] | length')
if [ $spider_count -gt 15 ]; then
    (>&2 echo "refusing to run on more than 15 spiders")
    exit 1
fi

if [ $spider_count -eq 0 ]; then
    (>&2 echo "no spiders modified (only deleted?)")
    exit 0
fi

if grep PLAYWRIGHT -q -m 1 $SPIDERS; then
    echo "Playwright detected. Installing requirements."
    playwright install-deps
    playwright install firefox
fi

RUN_DIR="/tmp/output"
EXIT_CODE=0
for file_changed in $SPIDERS
do
    if [[ $file_changed != locations/spiders/* ]]; then
        echo "${file_changed} is not a spider. Skipping."
        continue
    fi

    spider="${file_changed}"
    (>&2 echo "${spider} running ...")
    SPIDER_NAME=$(basename $spider)
    SPIDER_NAME=${SPIDER_NAME%.py}
    SPIDER_RUN_DIR="${RUN_DIR}/${SPIDER_NAME}"
    mkdir -p "${SPIDER_RUN_DIR}"

    LOGFILE="${SPIDER_RUN_DIR}/log.txt"
    OUTFILE="${SPIDER_RUN_DIR}/output.geojson"
    PARQUETFILE="${SPIDER_RUN_DIR}/output.parquet"
    FAILURE_REASON="success"

    timeout -k 5s 90s \
    scrapy runspider \
        -o "file://${OUTFILE}:geojson" \
        -o "file://${PARQUETFILE}:parquet" \
        --loglevel=INFO \
        --logfile="${LOGFILE}" \
        -s CLOSESPIDER_TIMEOUT=60 \
        -s CLOSESPIDER_ERRORCOUNT=1 \
        -s LOGSTATS_FILE=${SPIDER_RUN_DIR}/stats.json \
        $spider

    if [ ! $? -eq 0 ]; then
        (>&2 echo "${spider} hit shell timeout")
        EXIT_CODE=1
        FAILURE_REASON="timeout"
    elif grep -q "Spider closed (closespider_errorcount)" $LOGFILE; then
        (>&2 echo "${spider} exited with errors")
        EXIT_CODE=1
        FAILURE_REASON="exception"
    elif grep -q "Spider closed (closespider_timeout)" $LOGFILE; then
        (>&2 echo "${spider} exited because of timeout")
        FAILURE_REASON="timeout"
    fi

    aws --only-show-errors s3 cp ${LOGFILE} s3://${BUCKET}/ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/log.txt
    retval=$?
    if [ ! $retval -eq 0 ]; then
        (>&2 echo "log copy to s3 failed with exit code ${retval}")
        exit 1
    fi

    LOGFILE_URL="https://alltheplaces-data.openaddresses.io/ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/log.txt"
    echo "${spider} log: ${LOGFILE_URL}"

    if [ -f "$OUTFILE" ]; then
        FEATURE_COUNT=$(jq --raw-output '.item_scraped_count' ${SPIDER_RUN_DIR}/stats.json)

        if [ $FEATURE_COUNT == "null" ]; then
            FEATURE_COUNT="0"
        fi

        if [ $FEATURE_COUNT == "0" ]; then
            echo "${spider} has no output"
            FAILURE_REASON="no output"
            PR_COMMENT_BODY="${PR_COMMENT_BODY}|[\`$spider\`](https://github.com/alltheplaces/alltheplaces/blob/${GITHUB_SHA}/${spider})| (No Output) |Resulted in a \`${FAILURE_REASON}\` ([Log](${LOGFILE_URL}))|\\n"
            EXIT_CODE=1
            continue
        fi

        aws s3 cp --only-show-errors ${OUTFILE} s3://${BUCKET}/ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/output.geojson
        retval=$?
        if [ ! $retval -eq 0 ]; then
            (>&2 echo "output copy to s3 failed with exit code ${retval}")
            exit 1
        fi

        OUTFILE_URL="https://alltheplaces-data.openaddresses.io/ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/output.geojson"

        if grep -q 'Stored geojson feed' $LOGFILE; then
            echo "${spider} has ${FEATURE_COUNT} features: https://alltheplaces-data.openaddresses.io/map.html?show=${OUTFILE_URL}"
        fi

        aws s3 cp --only-show-errors ${PARQUETFILE} s3://${BUCKET}/ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/output.parquet
        retval=$?
        if [ ! $retval -eq 0 ]; then
            (>&2 echo "parquet copy to s3 failed with exit code ${retval}")
            exit 1
        fi

        PR_COMMENT_BODY="${PR_COMMENT_BODY}|[\`$spider\`](https://github.com/alltheplaces/alltheplaces/blob/${GITHUB_SHA}/${spider})|[${FEATURE_COUNT} items](${OUTFILE_URL}) ([Map](https://alltheplaces-data.openaddresses.io/map.html?show=${OUTFILE_URL}))|Resulted in a \`${FAILURE_REASON}\` ([Log](${LOGFILE_URL}))|\\n"
    else
        echo "${spider} has no output"
        FAILURE_REASON="no output"
        PR_COMMENT_BODY="${PR_COMMENT_BODY}|[\`$spider\`](https://github.com/alltheplaces/alltheplaces/blob/${GITHUB_SHA}/${spider})| (No Output) |Resulted in a \`${FAILURE_REASON}\` ([Log](${LOGFILE_URL}))|\\n"
        EXIT_CODE=1
    fi

    (>&2 echo "${spider} done")
done

if [[ ! "$(ls ${RUN_DIR})" ]]; then
    echo "Nothing ran. Exiting."
    echo $EXIT_CODE
fi

if [ -z "${GITHUB_TOKEN}" ]; then
    echo "No GITHUB_TOKEN set"
else
    if [ "${pull_request_number}" != "false" ]; then
        curl \
            -s \
            -XPOST \
            -H "Authorization: token ${GITHUB_TOKEN}" \
            -d "{\"body\":\"${PR_COMMENT_BODY}\"}" \
            "https://api.github.com/repos/alltheplaces/alltheplaces/issues/${pull_request_number}/comments"
        echo "Added a comment to pull https://github.com/alltheplaces/alltheplaces/pull/${pull_request_number}"
    else
        echo "Not posting to GitHub because no pull event number set"
    fi
fi

exit $EXIT_CODE
