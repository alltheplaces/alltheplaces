# -*- coding: utf-8 -*-
import ast
import json

import scrapy

from locations.items import GeojsonPointItem


class FreddysSpider(scrapy.Spider):
    name = "freddys"
    item_attributes = {"brand": "Freddy's", "brand_wikidata": "Q5496837"}
    allowed_domains = ["freddysusa.com"]
    start_urls = [
        "https://freddysusa.com/locations/?type=findmyfreddys&address=73034&distance=5000"
    ]

    def parse(self, response):
        script = response.xpath('//script/text()[contains(., "var locations")]').get()
        it = iter(script.splitlines())
        for line in it:
            if "var locations" in line:
                data = next(it)
                break
        data = ast.literal_eval("[" + data.rstrip(";\n"))
        for [link, lat, lon] in data:
            body = scrapy.Selector(text=link)
            url = body.xpath("//@href").get()
            meta = {"lat": lat, "lon": lon}
            yield scrapy.Request(url, meta=meta, callback=self.parse_store)

    def parse_store(self, response):
        for ldjson in response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).extract():
            if "LocalBusiness" in ldjson:
                break
        ldjson = json.loads(ldjson)
        storeName = response.xpath('//p[@class="storeName"]/text()').get()
        properties = {
            "ref": response.url.split("/")[-2],
            "lat": response.meta["lat"],
            "lon": response.meta["lon"],
            "website": response.url,
            "name": storeName,
            "phone": ldjson["telephone"],
            "addr_full": ldjson["address"]["streetAddress"],
            "city": ldjson["address"]["addressLocality"],
            "postcode": ldjson["address"]["postalCode"],
        }
        yield GeojsonPointItem(**properties)
