# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem


class FnbUSSpider(scrapy.Spider):
    name = "fnb_us"
    item_attributes = {"brand": "First National Bank", "brand_wikidata": "Q5426765"}
    allowed_domains = ["fnb-online.com"]
    start_urls = ("https://locations.fnb-online.com/sitemap.xml",)

    def parse(self, response):
        response.selector.remove_namespaces()
        for url in response.xpath("//loc/text()").extract():
            if url.count("/") == 4:
                # These are dead links
                meta = {"dont_redirect": True}
                yield scrapy.Request(url, callback=self.parse_store, meta=meta)

    def parse_store(self, response):
        script = response.xpath(
            '//script/text()[contains(.,"var location_data")]'
        ).get()
        start = script.index("var location_data =") + len("var location_data =")
        data = json.decoder.JSONDecoder().raw_decode(script, start)[0][0]

        properties = {
            "ref": data["id"],
            "lat": data["lat"],
            "lon": data["lng"],
            "name": data["name"],
            "addr_full": data["address"],
            "city": data["city"],
            "state": data["state"],
            "postcode": data["postalcode"],
            "country": data["country"],
            "phone": data["phone"],
            "website": response.url,
            "opening_hours": data["branchhours"],
        }
        yield GeojsonPointItem(**properties)
