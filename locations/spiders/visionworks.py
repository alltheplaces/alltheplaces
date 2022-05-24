# -*- coding: utf-8 -*-

import scrapy

from locations.items import GeojsonPointItem
from urllib.parse import urlencode

URL = "https://api.momentfeed.com/v1/analytics/api/llp.json?"


class VisionWorksSpider(scrapy.Spider):
    name = "visionworks"
    allowed_domains = ["visionworks.com", "api.momentfeed.com"]
    item_attributes = {"brand": "Visionworks", "brand_wikidata": "Q5422607"}
    start_urls = [
        "https://locations.visionworks.com/sitemap.xml",
    ]
    download_delay = 0.3
    custom_settings = {
        "USER_AGENT": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36",
    }

    def parse_store(self, response):
        data = response.json()
        store_data = data[0]["store_info"]

        properties = {
            "ref": store_data["corporate_id"],
            "name": store_data["name"],
            "addr_full": store_data["address"],
            "city": store_data["locality"],
            "state": store_data["region"],
            "postcode": store_data["postcode"].zfill(5),
            "country": store_data["country"],
            "lat": store_data["latitude"],
            "lon": store_data["longitude"],
            "phone": store_data["phone"],
            "website": store_data["website"],
        }

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()
        locations = response.xpath("//url/loc/text()").extract()

        for location_url in locations:
            # Store pages require extra javascript to load content (otherwise hit blank page)
            # let's bypass that with requests to their api instead
            base_url = URL
            path_components = location_url.split("/")
            address = (
                path_components[-1]
                .replace("+~", "&")
                .replace("-", " ")
                .replace("~", "-")
                .replace("_", ".")
            )
            locality = path_components[-2].replace("-", " ").replace("~", "-")
            state = path_components[-3]

            headers = {
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": "https://locations.visionworks.com",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "application/json, text/plain, */*",
                "Referer": "https://locations.visionworks.com/",
                "Connection": "keep-alive",
                "Content-Type": "application/json;charset=utf-8",
            }

            params = {
                "auth_token": "URTGGJIFYMDMAMXQ",
                "address": f"{address}",
                "locality": f"{locality}",
                "region": f"{state}",
                "pageSize": "1000",
                "multi_account": "true",
            }

            url = base_url + urlencode(params).replace("%2A", ",").replace(
                "-%23E201", ""
            )

            yield scrapy.http.Request(
                url=url, headers=headers, callback=self.parse_store
            )
