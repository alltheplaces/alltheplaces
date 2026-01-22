#!/bin/bash

generate_jwt() {
    # Generate a JWT for GitHub App authentication
    app_id="$1"
    private_key="$2"

    now=$(date +%s)
    iat=$((${now} - 60)) # Issues 60 seconds in the past
    exp=$((${now} + 600)) # Expires 10 minutes in the future

    b64enc() { openssl base64 | tr -d '=' | tr '/+' '_-' | tr -d '\n'; }

    header_json='{
        "typ":"JWT",
        "alg":"RS256"
    }'
    header=$( echo -n "${header_json}" | b64enc )

    payload_json="{
        \"iat\":${iat},
        \"exp\":${exp},
        \"iss\":\"${app_id}\"
    }"
    payload=$( echo -n "${payload_json}" | b64enc )

    header_payload="${header}"."${payload}"
    signature=$(
        openssl dgst -sha256 -sign <(echo -n "${private_key}") \
        <(echo -n "${header_payload}") | b64enc
    )

    echo "${header_payload}"."${signature}"
}

get_installation_token() {
    # Get an installation token using the JWT
    app_id="$1"
    private_key="$2"
    installation_id="$3"

    jwt=$(generate_jwt "$app_id" "$private_key")

    curl -s -X POST \
         -H "Authorization: Bearer ${jwt}" \
         -H "Accept: application/vnd.github.v3+json" \
         "https://api.github.com/app/installations/${installation_id}/access_tokens" \
         | jq -r '.token'
}

upload_to_s3() {
    # Upload a file to S3
    local file_path="$1"
    local s3_path="$2"

    uv run aws s3 cp --only-show-errors "${file_path}" "s3://${s3_path}"
    retval=$?
    if [ ! $retval -eq 0 ]; then
        (>&2 echo "uploading ${file_path} to s3 failed with exit code ${retval}")
        exit 1
    fi
}

upload_to_r2() {
    # Upload a file to R2
    local file_path="$1"
    local r2_path="$2"

    AWS_ACCESS_KEY_ID="${R2_ACCESS_KEY_ID}" \
    AWS_SECRET_ACCESS_KEY="${R2_SECRET_ACCESS_KEY}" \
    uv run aws s3 cp --endpoint-url="${R2_ENDPOINT_URL}" --only-show-errors "${file_path}" "s3://${r2_path}"
    retval=$?
    if [ ! $retval -eq 0 ]; then
        (>&2 echo "uploading ${file_path} to R2 failed with exit code ${retval}")
        exit 1
    fi
}

upload_file() {
    # Upload a file to a specified location (S3 and R2)
    local file_path="$1"
    local path="$2"

    upload_to_s3 "${file_path}" "${S3_BUCKET}/${path}"
    upload_to_r2 "${file_path}" "${R2_BUCKET}/${path}"
}

PR_COMMENT_BODY="I ran the spiders in this pull request and got these results:\\n\\n|Spider|Results|Log|\\n|---|---|---|\\n"

if [ -z "${GITHUB_APP_ID}" ] || [ -z "${GITHUB_APP_PRIVATE_KEY_BASE64}" ] || [ -z "${GITHUB_APP_INSTALLATION_ID}" ]; then
    echo "GitHub App credentials not set"
    exit 1
fi

# Get an access token for github interactions
private_key=$(echo "$GITHUB_APP_PRIVATE_KEY_BASE64" | base64 -d)
github_access_token=$(get_installation_token "${GITHUB_APP_ID}" "${private_key}" "${GITHUB_APP_INSTALLATION_ID}")

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

pr_file_changes=$(curl -sL --header "authorization: token ${github_access_token}" "https://api.github.com/repos/alltheplaces/alltheplaces/pulls/${pull_request_number}/files")

changed_filenames=$(echo -n "${pr_file_changes}" | jq -r '.[] | select(.status != "removed") | .filename')
retval=$?
if [ ! $retval -eq 0 ]; then
    (>&2 echo "checking file changes failed. response was ${pr_file_changes}")
    exit 1
fi
(>&2 echo "Changed files: ${changed_filenames}")

spiders=$(echo "${changed_filenames}" | grep "^locations/spiders/")

spider_count=$(echo "${spiders}" | wc -l)
if [ "${spider_count}" -gt 15 ]; then
    (>&2 echo "refusing to run on more than 15 spiders")
    exit 1
fi

if [ "${spider_count}" -eq 0 ]; then
    # Manually run a couple spiders when uv.lock or pyproject.toml changes
    if echo "${changed_filenames}" | grep -q "pyproject.toml" || echo "${changed_filenames}" | grep -q "uv.lock"; then
        echo "pyproject.toml or uv.lock changed. Running a couple spiders."
        spiders=$'locations/spiders/the_works.py\nlocations/spiders/the_coffee_club_au.py\nlocations/spiders/woods_coffee_us.py'
    else
        (>&2 echo "no spiders modified (only deleted?)")
        exit 0
    fi
fi

if grep PlaywrightSpider -q -m 1 $spiders; then
    echo "Playwright spider detected. Installing requirements."
    uv run playwright install-deps
    uv run playwright install firefox
fi

if grep CamoufoxSpider -q -m 1 $spiders; then
    echo "Camoufox spider detected. Installing requirements."
    uv run camoufox fetch
fi

RUN_DIR="/tmp/output"
EXIT_CODE=0
for file_changed in $spiders
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
    NDGEOJSON="${SPIDER_RUN_DIR}/output.ndgeojson"
    STATSFILE="${SPIDER_RUN_DIR}/stats.json"
    FAILURE_REASON="success"

    timeout -k 1m 150s \
    uv run scrapy runspider \
        -o "file://${OUTFILE}:geojson" \
        -o "file://${NDGEOJSON}:ndgeojson" \
        --loglevel=INFO \
        --logfile="${LOGFILE}" \
        -s CLOSESPIDER_TIMEOUT=120 \
        -s CLOSESPIDER_ERRORCOUNT=1 \
        -s LOGSTATS_FILE="${STATSFILE}" \
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

    upload_file "${LOGFILE}" "ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/log.txt"

    LOGFILE_URL="https://alltheplaces-data.openaddresses.io/ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/log.txt"
    echo "${spider} log: ${LOGFILE_URL}"

    if [ -f "${OUTFILE}" ]; then
        upload_file "${OUTFILE}" "ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/output.geojson"
        upload_file "${NDGEOJSON}" "ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/output.ndgeojson"
        OUTFILE_URL="https://alltheplaces-data.openaddresses.io/ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/output.geojson"

        if [ -f "${STATSFILE}" ]; then
            upload_file "${STATSFILE}" "ci/${CODEBUILD_BUILD_ID}/${SPIDER_NAME}/stats.json"

            FEATURE_COUNT=$(jq --raw-output '.item_scraped_count' ${SPIDER_RUN_DIR}/stats.json)

            if [ "${FEATURE_COUNT}" == "null" ]; then
                FEATURE_COUNT="0"
            fi

            # Short compare: show only an arrow and delta (e.g. "↑3" or "↓2").
            # Also set a small link to the previous run stats when available.
            COMPARE_TEXT=""
            latest_run_id=$(curl -s 'https://data.alltheplaces.xyz/runs/latest.json' | jq -r '.run_id' 2>/dev/null)
            if [ -n "${latest_run_id}" ] && [ "${latest_run_id}" != "null" ]; then
                prev_stats_url="https://alltheplaces-data.openaddresses.io/runs/${latest_run_id}/stats/${SPIDER_NAME}.json"
                prev_count=$(curl -s "${prev_stats_url}" | jq --raw-output '.item_scraped_count' 2>/dev/null)
                if [ -z "${prev_count}" ] || [ "${prev_count}" = "null" ]; then
                    # Don't show compare info if we can't get previous count
                    COMPARE_TEXT=""
                fi

                if [ -n "${FEATURE_COUNT}" ]; then
                    diff=$((FEATURE_COUNT - prev_count))
                    if [ "$diff" -gt 0 ]; then
                        COMPARE_TEXT=" [↑${diff}](${prev_stats_url})"
                    elif [ "$diff" -lt 0 ]; then
                        # show positive number after down arrow
                        absdiff=${diff#-}
                        COMPARE_TEXT=" [↓${absdiff}](${prev_stats_url})"
                    else
                        COMPARE_TEXT=" [→0](${prev_stats_url})"
                    fi
                fi
            fi

            if [ "${FEATURE_COUNT}" == "0" ]; then
                echo "${spider} has no output"
                FAILURE_REASON="no output"
                PR_COMMENT_BODY="${PR_COMMENT_BODY}|[\`$spider\`](https://github.com/alltheplaces/alltheplaces/blob/${GITHUB_SHA}/${spider})| (No Output) ${COMPARE_TEXT} |Resulted in a \`${FAILURE_REASON}\` ([Log](${LOGFILE_URL}))|\\n"
                EXIT_CODE=1
                continue
            fi

            STATS_WARNINGS=""
            STATS_ERRORS=""

            # We expect items to have a category
            missing_category=$(jq '."atp/category/missing" // 0' "${STATSFILE}")
            if [ $missing_category -gt 0 ]; then
                STATS_ERRORS="${STATS_ERRORS}<li>🚨 Category is not set on ${missing_category} items</li>"
            fi

            # Warn if items are missing geometry
            missing_geometry=$(jq '."atp/field/geometry/missing" // 0' "${STATSFILE}")
            if [ $missing_geometry -gt 0 ]; then
                STATS_WARNINGS="${STATS_WARNINGS}<li>⚠️ Geometry is missing on ${missing_geometry} items</li>"
            fi

            # Error if items have invalid geometry
            invalid_geometry=$(jq '."atp/field/geometry/invalid" // 0' "${STATSFILE}")
            if [ $invalid_geometry -gt 0 ]; then
                STATS_ERRORS="${STATS_ERRORS}<li>🚨 Geometry is invalid on ${invalid_geometry} items</li>"
            fi

            # Error if items have invalid website
            invalid_website=$(jq '."atp/field/website/invalid" // 0' "${STATSFILE}")
            if [ $invalid_website -gt 0 ]; then
                STATS_ERRORS="${STATS_ERRORS}<li>🚨 Website is invalid on ${invalid_website} items</li>"
            fi

            # Warn if items were fetched using Zyte
            zyte_fetched=$(jq '."scrapy-zyte-api/success" // 0' "${STATSFILE}")
            if [ $zyte_fetched -gt 0 ]; then
                STATS_WARNINGS="${STATS_WARNINGS}<li>⚠️ ${zyte_fetched} requests were made using Zyte</li>"
            fi

            # Warn if more than 30% of the items scraped were dropped by the dupe filter
            dupe_dropped=$(jq '."atp/duplicate_count" // 0' "${STATSFILE}")
            dupe_percent=$(awk -v dd="${dupe_dropped}" -v fc="${FEATURE_COUNT}" 'BEGIN { printf "%.2f", (dd / fc) * 100 }')
            if awk -v dp="${dupe_percent}" 'BEGIN { exit !(dp > 30) }'; then
                STATS_WARNINGS="${STATS_WARNINGS}<li>⚠️ ${dupe_dropped} items (${dupe_percent}%) were dropped by the dupe filter</li>"
            fi

            # Warn if the image URL is not very unique across all the outputs
            unique_image_urls=$(jq '.features | map(.properties.image) | map(select(. != null)) | unique | length' ${OUTFILE})
            unique_image_url_rate=$(awk -v uiu="${unique_image_urls}" -v fc="${FEATURE_COUNT}" 'BEGIN { if (fc > 0 && uiu > 0) { printf "%.2f", (uiu / fc) * 100 } else { printf "0.00" } }')
            if awk -v uiu="${unique_image_urls}" -v uir="${unique_image_url_rate}" 'BEGIN { exit !(uir < 50 && uiu > 0) }'; then
                STATS_WARNINGS="${STATS_WARNINGS}<li>⚠️ Only ${unique_image_urls} (${unique_image_url_rate}%) unique image URLs</li>"
            fi

            # Warn if the phone number is not very unique across all the outputs
            unique_phones=$(jq '.features | map(.properties.phone) | map(select(. != null)) | unique | length' ${OUTFILE})
            unique_phone_rate=$(awk -v up="${unique_phones}" -v fc="${FEATURE_COUNT}" 'BEGIN { if (fc > 0 && up > 0) { printf "%.2f", (up / fc) * 100 } else { printf "0.00" } }')
            if awk -v up="${unique_phones}" -v upr="${unique_phone_rate}" 'BEGIN { exit !(upr < 90 && up > 0) }'; then
                STATS_WARNINGS="${STATS_WARNINGS}<li>⚠️ Only ${unique_phones} (${unique_phone_rate}%) unique phone numbers</li>"
            fi

            # Warn if the email is not very unique across all the outputs
            unique_emails=$(jq '.features | map(.properties.email) | map(select(. != null)) | unique | length' ${OUTFILE})
            unique_email_rate=$(awk -v ue="${unique_emails}" -v fc="${FEATURE_COUNT}" 'BEGIN { if (fc > 0 && ue > 0) { printf "%.2f", (ue / fc) * 100 } else { printf "0.00" } }')
            if awk -v ue="${unique_emails}" -v uer="${unique_email_rate}" 'BEGIN { exit !(uer < 90 && ue > 0) }'; then
                STATS_WARNINGS="${STATS_WARNINGS}<li>⚠️ Only ${unique_emails} (${unique_email_rate}%) unique email addresses</li>"
            fi

            num_warnings=$(echo "${STATS_WARNINGS}" | grep -o "</li>" | wc -l)
            num_errors=$(echo "${STATS_ERRORS}" | grep -o "</li>" | wc -l)
            if [ "${num_errors}" -gt 0 ]; then
                FAILURE_REASON="stats"
                EXIT_CODE=1
            fi

            if [ "${num_errors}" -gt 0 ] || [ "${num_warnings}" -gt 0 ]; then
                # Include details in an expandable section if there are warnings or errors
                PR_COMMENT_BODY="${PR_COMMENT_BODY}|[\`$spider\`](https://github.com/alltheplaces/alltheplaces/blob/${GITHUB_SHA}/${spider})|[${FEATURE_COUNT} items](${OUTFILE_URL}) ([Map](https://alltheplaces.xyz/preview.html?show=${OUTFILE_URL})) ${COMPARE_TEXT}|<details><summary>Resulted in a \`${FAILURE_REASON}\` ([Log](${LOGFILE_URL})) 🚨${num_errors} ⚠️${num_warnings}</summary><ul>${STATS_ERRORS}${STATS_WARNINGS}</ul></details>|\\n"
            else
                PR_COMMENT_BODY="${PR_COMMENT_BODY}|[\`$spider\`](https://github.com/alltheplaces/alltheplaces/blob/${GITHUB_SHA}/${spider})|[${FEATURE_COUNT} items](${OUTFILE_URL}) ([Map](https://alltheplaces.xyz/preview.html?show=${OUTFILE_URL})) ${COMPARE_TEXT}|Resulted in a \`${FAILURE_REASON}\` ([Log](${LOGFILE_URL})) ✅|\\n"
            fi
            continue
        else
            (>&2 echo "${spider} has no stats file")
            STATS_WARNINGS=""
            STATS_ERRORS=""
        fi

        PR_COMMENT_BODY="${PR_COMMENT_BODY}|[\`$spider\`](https://github.com/alltheplaces/alltheplaces/blob/${GITHUB_SHA}/${spider})|[${FEATURE_COUNT} items](${OUTFILE_URL}) ([Map](https://alltheplaces.xyz/preview.html?show=${OUTFILE_URL}))|Resulted in a \`${FAILURE_REASON}\` ([Log](${LOGFILE_URL}))|\\n"
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

if [ "${pull_request_number}" != "false" ]; then
    curl \
        -s \
        -XPOST \
        -H "Authorization: token ${github_access_token}" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "{\"body\":\"${PR_COMMENT_BODY}\"}" \
        "https://api.github.com/repos/alltheplaces/alltheplaces/issues/${pull_request_number}/comments" > /dev/null

    if [ ! $? -eq 0 ]; then
        (>&2 echo "comment post failed")
        exit 1
    fi

    echo "Added a comment to pull https://github.com/alltheplaces/alltheplaces/pull/${pull_request_number}"
else
    echo "Not posting to GitHub because no pull event number set"
fi

exit $EXIT_CODE
