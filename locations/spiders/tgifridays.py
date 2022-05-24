# -*- coding: utf-8 -*-
import datetime
import re
import json

import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {
    "Monday": "Mo",
    "Tuesday": "Tu",
    "Wednesday": "We",
    "Thursday": "Th",
    "Friday": "Fr",
    "Saturday": "Sa",
    "Sunday": "Su",
}


class TGIFridaySpider(scrapy.Spider):
    download_delay = 0.2
    name = "tgifridays"
    item_attributes = {"brand": "TGI Friday's", "brand_wikidata": "Q1524184"}
    allowed_domains = ["tgifridays.com"]
    start_urls = ("https://locations.tgifridays.com/sitemap.xml",)

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            if hour["opens"] in ("Closed", ""):
                continue
            elif hour["closes"] in ("Closed", ""):
                continue
            else:
                opening_hours.add_range(
                    day=hour["dayOfWeek"].replace("http://schema.org/", "")[:2],
                    open_time=hour["opens"],
                    close_time=hour["closes"],
                    time_format="%I:%M%p",
                )

        return opening_hours.as_opening_hours()

    def parse_store(self, response):
        # The JSON blob has an extra "}\r\n" at the end
        data = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).extract_first()[:-3]
        )

        properties = {
            "addr_full": data["address"]["streetAddress"],
            "phone": data["telephone"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "ref": data["@id"],
            "website": data["url"],
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": data["name"],
        }

        hours = self.parse_hours(data.get("openingHoursSpecification", []))
        if hours:
            properties["opening_hours"] = hours

        yield GeojsonPointItem(**properties)

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        for path in city_urls:
            if path.count("/") == 5:
                yield scrapy.Request(
                    path.strip(),
                    callback=self.parse_store,
                )
