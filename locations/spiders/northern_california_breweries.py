# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json
import re


class NorthernCaliforniaBreweriesSpider(scrapy.Spider):
    name = "northern_california_breweries"
    allowed_domains = ["projects.sfchronicle.com"]
    start_urls = ("http://projects.sfchronicle.com/2017/brewery-map/",)

    def parse(self, response):
        beerData = response.xpath("//*[text()[contains(.,'beerData')]]").extract_first()
        matches = re.search(r"var beerData = (\[(.*)\])", beerData)
        jsonData = matches.group(0).replace("var beerData = ", "")
        breweryList = json.loads(jsonData)

        for item in breweryList:
            latitude = None
            longitude = None

            if item.get("Latitude") is not None:
                latitude = float(item.get("Latitude"))

            if item.get("Longitude") is not None:
                longitude = float(item.get("Longitude"))

            yield GeojsonPointItem(
                ref=item.get("Brewery"),
                lat=latitude,
                lon=longitude,
                addr_full=item.get("Address"),
                city=item.get("City"),
                state="CA",
                website=item.get("Website"),
            )
