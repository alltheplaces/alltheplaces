# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json
from parsel import Selector


class CoopersHawkSpider(scrapy.Spider):
    name = "coopers_hawk"
    item_attributes = {"brand": "Cooper's Hawk", "brand_wikidata": "Q64411347"}
    allowed_domains = ["chwinery.com"]
    start_urls = ("https://chwinery.com/locations",)

    def parse(self, response):
        dna_json = json.loads(response.css(".gm-map").xpath("@data-dna").get())
        markers = [x for x in dna_json if x["type"] == "markers"]
        for marker in markers:
            content = Selector(text=marker["options"]["infoWindowOptions"]["content"])
            address_lines = content.css(".location-capsule__body > p::text").getall()
            city_name, extra = address_lines[1].strip().split(", ")
            state, postcode = extra.split(" ")

            yield GeojsonPointItem(
                lat=marker["locations"][0]["lat"],
                lon=marker["locations"][0]["lng"],
                ref=marker["locations"][0]["id"].split("-")[0],
                name=content.css(".location-capsule__heading::text").get().strip(),
                addr_full=address_lines[0].strip(),
                city=city_name,
                state=state,
                postcode=postcode,
                website=content.xpath('//a[text() = "Location Details"]/@href').get(),
            )
