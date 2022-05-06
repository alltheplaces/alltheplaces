# -*- coding: utf-8 -*-
from scrapy.spiders import SitemapSpider
from scrapy.downloadermiddlewares.retry import get_retry_request

import re
import json

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class DillardsSpider(SitemapSpider):
    name = "dillards"
    item_attributes = {"brand": "Dillard's", "brand_wikidata": "Q844805"}
    allowed_domains = ["www.dillards.com"]
    sitemap_urls = ("https://www.dillards.com/sitemap/sitemap_storeLocator_1.xml",)
    download_delay = 0.5

    sitemap_rules = [(r"https://www.dillards.com/stores/.*/.*", "parse")]

    def parse(self, response):
        if "Access Denied" in response.text:
            return get_retry_request(response.request, spider=self, reason="throttle")

        ldjson = response.xpath(
            '//script[@type="application/ld+json"]/text()[contains(.,"DepartmentStore")]'
        ).get()
        data = json.loads(ldjson)

        script = response.xpath(
            '//script/text()[contains(.,"__INITIAL_STATE__")]'
        ).get()
        script_data = json.decoder.JSONDecoder().raw_decode(script, script.index("{"))[
            0
        ]
        lat = script_data["contentData"]["store"]["latitude"]
        lon = script_data["contentData"]["store"]["longitude"]

        hours = OpeningHours()
        for row in data["openingHoursSpecification"]:
            day = row["dayOfWeek"]["name"][:2]
            hours.add_range(day, row["opens"], row["closes"], "%I:%M %p")

        properties = {
            "ref": response.css(".storeNumber::text").get(),
            "lat": lat,
            "lon": lon,
            "website": response.url,
            "name": data["name"],
            "phone": data["telephone"],
            "street_address": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "opening_hours": hours.as_opening_hours(),
        }
        return GeojsonPointItem(**properties)
