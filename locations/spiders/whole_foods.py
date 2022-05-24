# -*- coding: utf-8 -*-
import logging

import scrapy
import re

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours
import json


class WholeFoodsSpider(scrapy.Spider):
    name = "whole_foods"
    item_attributes = {"brand": "Whole Foods", "brand_wikidata": "Q1809448"}
    allowed_domains = ["wholefoodsmarket.com", "wholefoodsmarket.co.uk"]
    start_urls = (
        "https://www.wholefoodsmarket.com/sitemap/sitemap-stores.xml",
        "https://www.wholefoodsmarket.co.uk/sitemap.xml",
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath("//url/loc/text()").extract()
        us_regex = re.compile(r"https://www.wholefoodsmarket.com/stores/\S+")
        uk_regex = re.compile(r"https://www.wholefoodsmarket.co.uk/stores/\S+")
        for path in city_urls:
            if re.search(us_regex, path):
                yield scrapy.Request(path.strip(), callback=self.parse_us_store)
            elif re.search(uk_regex, path):
                yield scrapy.Request(path.strip(), callback=self.parse_uk_store)
            else:
                pass

    def parse_us_store(self, response):
        # Handle redirects to main page (closed store) and UK pages
        if response.request.meta.get("redirect_urls"):
            return

        store_json = json.loads(
            response.xpath(
                '//script[@type="application/ld+json"]/text()'
            ).extract_first()
        )
        yield GeojsonPointItem(
            ref=response.url.split("/")[-1],
            name=response.xpath("//h1/text()").extract_first().strip(),
            lat=float(store_json["geo"]["latitude"]),
            lon=float(store_json["geo"]["longitude"]),
            addr_full=store_json["address"]["streetAddress"],
            city=store_json["address"]["addressLocality"],
            state=store_json["address"]["addressRegion"],
            postcode=store_json["address"]["postalCode"],
            phone=store_json["telephone"],
            website=response.url,
            opening_hours=self.parse_hours(store_json["openingHoursSpecification"]),
        )

    def parse_hours(self, hours):
        opening_hours = OpeningHours()

        for hour in hours:
            opening_hours.add_range(
                day=hour["dayOfWeek"].split("/")[-1][0:2],
                open_time=hour["opens"],
                close_time=hour["closes"],
            )

        return opening_hours.as_opening_hours()

    def parse_uk_store(self, response):
        # Handle redirects to main page (closed store)
        if response.request.meta.get("redirect_urls"):
            return

        store_text = response.xpath(
            '//script[@type="text/javascript" and contains(text(), "storeAPIData")]/text()'
        ).extract_first()
        store_json = json.loads(
            store_text[store_text.find("{") : store_text.rfind("}") + 1]
        )["initialProps"]["siteData"]["storeAPIData"]

        # Coordinates are listed as [lon, lat]
        yield GeojsonPointItem(
            ref=store_json["folder"],
            name=store_json["name"],
            lat=float(store_json["geo_location"]["coordinates"][1]),
            lon=float(store_json["geo_location"]["coordinates"][0]),
            addr_full=store_json["address"],
            city=store_json["city"],
            state=store_json["state"],
            postcode=store_json["zip_code"],
            country=store_json["country"],
            phone=store_json["phone"],
            website=response.url,
            opening_hours=store_json["hours"],
        )
