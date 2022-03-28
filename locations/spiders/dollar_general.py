# -*- coding: utf-8 -*-
import gzip
import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class DollarGeneralSpider(scrapy.Spider):
    name = "dollar_general"
    item_attributes = {"brand": "Dollar General", "brand_wikidata": "Q145168"}
    allowed_domains = ["dollargeneral.com"]
    start_urls = ["https://stores.dollargeneral.com/sitemap.xml.gz"]

    def parse(self, response):
        xml = scrapy.Selector(type="xml", text=gzip.decompress(response.body))
        xml.remove_namespaces()
        for url in xml.xpath("//loc/text()").extract():
            if url.count("/") == 6:
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        ldjson = response.xpath(
            '//script[@type="application/ld+json"]/text()[contains(.,"GroceryStore")]'
        ).get()
        # hacky removal of javascript comments from json
        ldjson = re.sub(r" //.*", "", ldjson)
        data = json.loads(ldjson)

        hours = OpeningHours()
        for row in data["openingHoursSpecification"]:
            opens = row["opens"]
            closes = row["closes"]
            if opens == "":
                continue
            if closes == "24:00":
                closes = "00:00"
            for day in row["dayOfWeek"]:
                hours.add_range(day[:2], opens, closes)

        properties = {
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "ref": data["@id"],
            "name": data["name"],
            "website": data["url"],
            "phone": data["telephone"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "opening_hours": hours.as_opening_hours(),
        }
        yield GeojsonPointItem(**properties)
