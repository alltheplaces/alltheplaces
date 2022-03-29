# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem


class MarathonScraper(scrapy.Spider):
    name = "marathon"
    item_attributes = {"brand": "Marathon Petroleum", "brand_wikidata": "Q458363"}

    start_urls = ["https://marathon.shotgunflat.com/data.txt"]

    def parse(self, response):
        for row in response.text.split("|`,"):
            if row == "":
                continue

            (name, address, lat, lon, slug, city, state, zip_code, phone) = row.split(
                "|"
            )

            if len(zip_code) == 9:
                zip_code = f"{zip_code[0:5]}-{zip_code[5:]}"

            yield GeojsonPointItem(
                lat=lat,
                lon=lon,
                ref=f"{slug}-{phone}",
                name=name,
                addr_full=address,
                city=city,
                state=state,
                postcode=zip_code,
                country="US",
                phone=phone,
                extras={
                    "amenity:fuel": True,
                },
            )
