import json
import re

import scrapy

from locations.items import Feature


class NorthernCaliforniaBreweriesSpider(scrapy.Spider):
    name = "northern_california_breweries"
    allowed_domains = ["projects.sfchronicle.com"]
    start_urls = ("http://projects.sfchronicle.com/2017/brewery-map/",)

    def parse(self, response):
        beer_data = response.xpath("//*[text()[contains(.,'beerData')]]").extract_first()
        matches = re.search(r"var beerData = (\[(.*)\])", beer_data)
        json_data = matches.group(0).replace("var beerData = ", "")
        brewery_list = json.loads(json_data)

        for item in brewery_list:
            latitude = None
            longitude = None

            if item.get("Latitude") is not None:
                latitude = float(item.get("Latitude"))

            if item.get("Longitude") is not None:
                longitude = float(item.get("Longitude"))

            yield Feature(
                ref=item.get("Brewery"),
                lat=latitude,
                lon=longitude,
                street_address=item.get("Address"),
                city=item.get("City"),
                state="CA",
                country="US",
                website=item.get("Website"),
            )
