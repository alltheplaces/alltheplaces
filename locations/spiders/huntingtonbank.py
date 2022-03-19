# -*- coding: utf-8 -*-
import json

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class HuntingtonBankSpider(scrapy.Spider):
    name = "huntingtonbank"
    item_attributes = {"brand": "Huntington Bank", "brand_wikidata": "Q798819"}
    allowed_domains = ["www.huntington.com"]
    start_urls = ["https://www.huntington.com/~/media/SEO_Files/sitemap.xml"]

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; CrOS aarch64 14324.72.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.91 Safari/537.36"
    }
    custom_settings = {"DEFAULT_REQUEST_HEADERS": headers}

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if "branch-info" in url:
                yield scrapy.Request(url, callback=self.parse_store)

    def parse_store(self, response):
        ldjson = response.xpath(
            '//script[@type="application/ld+json"]/text()[contains(.,"@context")]'
        ).get()
        if ldjson is None:
            return
        [data] = json.loads(ldjson)

        hours = OpeningHours()
        if data["openingHoursSpecification"] is not None:
            for row in data["openingHoursSpecification"]:
                day = row["dayOfWeek"].split("/")[-1][:2]
                hours.add_range(day, row["opens"], row["closes"], "%H:%M:%S")

        properties = {
            "ref": response.xpath("//@data-branch-id").get(),
            "lat": data["geo"]["latitude"],
            "lon": data["geo"]["longitude"],
            "name": data["name"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "postcode": data["address"]["postalCode"],
            "country": data["address"]["addressCountry"],
            "opening_hours": hours.as_opening_hours(),
            "website": data["url"],
            "phone": data["telephone"],
            "extras": {"fax": data["faxNumber"]},
        }
        yield GeojsonPointItem(**properties)
