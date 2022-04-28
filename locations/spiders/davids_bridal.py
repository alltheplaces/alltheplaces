# -*- coding: utf-8 -*-
import re
import json

import scrapy
from scrapy.downloadermiddlewares.retry import get_retry_request

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


DAY_MAPPING = {"Mo": 0, "Tu": 0, "We": 0, "Th": 0, "Fr": 0, "Sa": 1, "Su": 2}


class DavidsBridalSpider(scrapy.Spider):
    name = "davids_bridal"
    item_attributes = {"brand": "Davids Bridal", "brand_wikidata": "Q5230388"}
    allowed_domains = ["www.davidsbridal.com"]
    start_urls = ["https://www.davidsbridal.com/DBIStoresDirectoryView"]
    download_delay = 0.3

    def parse_hours(self, hours):
        opening_hours = OpeningHours()
        for day in DAY_MAPPING:
            open_close = hours[DAY_MAPPING[day]]
            if open_close.lower() in ["closed", "", "-"]:
                continue
            else:
                open_time, close_time = re.split(r" [-\u2013] ", open_close)
                open_time = open_time.replace(".", ":")
                close_time = close_time.replace(".", ":")
                if ":" not in open_time:
                    open_time = open_time.replace("am", ":00am")
                    open_time = open_time.replace("pm", ":00pm")
                if ":" not in close_time:
                    close_time = close_time.replace("am", ":00am")
                    close_time = close_time.replace("pm", ":00pm")
                opening_hours.add_range(
                    day=day,
                    open_time=open_time,
                    close_time=close_time,
                    time_format="%I:%M%p",
                )

        return opening_hours.as_opening_hours()

    def parse(self, response):
        locations = response.xpath('//div[@class="span6"]/a/@href').extract()
        for location in locations:
            yield scrapy.Request(location, callback=self.parse_store)

    def parse_store(self, response):
        if not response.text:
            yield get_retry_request(response.request, spider=self, reason="empty")
            return

        ldjson = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract_first()
        # Corrupted json in holiday hours
        ldjson = re.sub(r'</?br/?>.*"$', '"', ldjson, flags=re.M)
        store_data = json.loads(ldjson)

        properties = {
            "ref": re.search(r"stLocId=([0-9]+)", response.url).group(1),
            "name": store_data["name"],
            "addr_full": store_data["address"]["streetAddress"],
            "city": store_data["address"]["addressLocality"],
            "state": store_data["address"]["addressRegion"],
            "postcode": store_data["address"]["postalCode"],
            "country": store_data["address"]["addressCountry"],
            "phone": store_data["telephone"],
            "website": response.url,
            "lat": store_data["geo"].get("latitude", ""),
            "lon": store_data["geo"].get("longitude", ""),
        }

        hours = store_data.get("openingHours")
        if hours:
            properties["opening_hours"] = self.parse_hours(hours)

        yield GeojsonPointItem(**properties)
