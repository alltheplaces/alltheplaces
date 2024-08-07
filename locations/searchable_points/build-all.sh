#!/usr/bin/env bash

if ! command -v unzip &> /dev/null
then
    echo "unzip could not be found"
    exit 1
fi


if ! command -v ogr2ogr &> /dev/null
then
    echo "ogr2ogr could not be found. You may want to add the gdal-bin package"
    exit 1
fi

# Retrieve data, only if not available
if [ ! -f ne_10m_admin_0_countries_lakes.zip ]; then
    curl 'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries_lakes.zip' \
    -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
    -H 'accept-language: en-GB,en;q=0.9,en-US;q=0.8,de;q=0.7,es;q=0.6,fr;q=0.5' \
    -H 'dnt: 1' \
    -H 'priority: u=0, i' \
    -H 'referer: https://www.naturalearthdata.com/' \
    -H 'sec-ch-ua: "Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"' \
    -H 'sec-ch-ua-mobile: ?0' \
    -H 'sec-ch-ua-platform: "Windows"' \
    -H 'sec-fetch-dest: document' \
    -H 'sec-fetch-mode: navigate' \
    -H 'sec-fetch-site: cross-site' \
    -H 'sec-fetch-user: ?1' \
    -H 'sec-gpc: 1' \
    -H 'upgrade-insecure-requests: 1' \
    -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36' > ne_10m_admin_0_countries_lakes.zip
fi

unzip -n ne_10m_admin_0_countries_lakes.zip
