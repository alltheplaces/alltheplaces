# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.user_agents import BROSWER_DEFAULT


class LibertyMutualSpider(scrapy.Spider):
    name = "liberty_mutual"
    item_attributes = {"brand": "Liberty Mutual", "brand_wikidata": "Q1516450"}
    allowed_domains = ["www.libertymutual.com"]
    start_urls = ["http://www.libertymutual.com/office-sitemap.xml"]
    download_delay = 10
    custom_settings = {"CONCURRENT_REQUESTS": "1"}
    user_agent = BROSWER_DEFAULT

    def parse_store(self, response):
        data = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            response.text,
        )

        if data:
            json_data = json.loads(data.group(1))
            store_data = json_data["props"]["pageProps"]["office"]
            lon, lat = store_data["location"]["coordinates"]
            properties = {
                "name": store_data["name"],
                "ref": store_data["officeCode"],
                "addr_full": store_data["address"]["street"],
                "city": store_data["address"]["city"],
                "state": store_data["address"]["state"]["code"],
                "postcode": store_data["address"]["zip"],
                "phone": store_data.get("phones", {})
                .get("primary", {})
                .get("number", ""),
                "website": store_data.get("url") or response.url,
                "lat": lat,
                "lon": lon,
            }

            yield GeojsonPointItem(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()
        urls = [
            x for x in response.xpath("//url/loc/text()").extract() if x.count("/") > 4
        ]

        for url in urls:
            yield scrapy.Request(url, callback=self.parse_store)
