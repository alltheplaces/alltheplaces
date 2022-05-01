# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem

CITIES = ["Ashtabula", "Columbus", "Dayton", "Elyria", "Youngstown"]


class MarcsSpider(scrapy.Spider):
    name = "marcs"
    item_attributes = {"brand": "Marc's", "brand_wikidata": "Q17080259"}
    allowed_domains = ["marcs.com"]
    start_urls = ["https://www.marcs.com/store-finder"]

    def parse(self, response):
        search_name = response.xpath('//input/@name[contains(., "address")]').get()
        radius_name = response.xpath('//select/@name[contains(., "radius")]').get()
        submit_name = response.xpath('//input/@name[contains(., "submit")]').get()
        for city in CITIES:
            yield scrapy.FormRequest.from_response(
                response,
                formdata={search_name: city, radius_name: "50", submit_name: "Submit"},
                callback=self.parse_store_search,
            )

    def parse_store_search(self, response):
        for href in response.xpath('//div[@class="store-list"]//@href').extract():
            yield scrapy.Request(response.urljoin(href), callback=self.parse_store)

    def parse_store(self, response):
        map_script = response.xpath('//script/text()[contains(.,"var lng")]').get()
        lat = re.search("var lat = '(.*)';", map_script).group(1)
        lon = re.search("var lng = '(.*)';", map_script).group(1)

        ldjson = response.xpath(
            '//script[@type="application/ld+json"]/text()[contains(.,\'"Store"\')]'
        ).get()
        data = json.decoder.JSONDecoder().raw_decode(ldjson, ldjson.index("{"))[0]

        properties = {
            "ref": response.url,
            "lat": lat,
            "lon": lon,
            "name": data["name"],
            "website": response.url,
            "phone": data["telephone"],
            "addr_full": data["address"]["streetAddress"],
            "city": data["address"]["addressLocality"],
            "state": data["address"]["addressRegion"],
            "opening_hours": "; ".join(data["openingHours"]),
        }
        yield GeojsonPointItem(**properties)
