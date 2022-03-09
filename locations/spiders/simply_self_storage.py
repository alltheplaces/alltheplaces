# -*- coding: utf-8 -*-
import json
import re
from datetime import datetime

import scrapy

from locations.items import GeojsonPointItem


class SimplySelfStorageSpider(scrapy.Spider):
    name = "simply_self_storage"
    item_attributes = {"brand": "Simply Self Storage"}
    allowed_domains = ["simplyss.com"]
    start_urls = ("https://www.simplyss.com/site_map/",)

    def parse(self, response):
        store_urls = response.css(
            "a.main-page-anchor[href*='/locations/'] + ul a.grey-anchor::attr(href)"
        )
        for store_url in store_urls:
            yield scrapy.Request(
                store_url.extract(),
                callback=self.parse_store,
            )

    def parse_store(self, response):
        props = json.loads(
            response.css("script[type='application/ld+json']::text").extract_first()
        )
        yield GeojsonPointItem(
            lat=float(props["geo"]["latitude"]),
            lon=float(props["geo"]["longitude"]),
            name=props["name"],
            addr_full=props["address"]["streetAddress"],
            city=props["address"]["addressLocality"],
            state=props["address"]["addressRegion"],
            postcode=props["address"]["postalCode"],
            country=props["address"]["addressCountry"],
            phone=props["contactPoint"]["telephone"],
            website=response.url,
            opening_hours=self.convert_opening_hours(props["openingHours"]),
            ref=response.url,
        )

    def convert_opening_hours(self, hours_str):
        """Convert schema.org hours to OSM opening_hours"""
        hour_groups = []
        for hour_group in re.split(r"(?<=M)\s", hours_str):
            # Ignore closed statements
            if "Closed" in hour_group:
                continue
            weekdays, hours = re.split(r"\s(?=\d)", hour_group)
            weekday_list = weekdays.split(", ")
            if len(weekday_list) > 1:
                weekday_str = f"{weekday_list[0]}-{weekday_list[-1]}"
            else:
                weekday_str = weekday_list[0]
            hour_times = [
                datetime.strptime(hour_str, "%I:%M%p").strftime("%H:%M")
                for hour_str in hours.split("-")
            ]
            hour_groups.append(f"{weekday_str} {'-'.join(hour_times)}")
        return "; ".join(hour_groups)
