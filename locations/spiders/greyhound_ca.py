# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem


class GreyhoundCanadaSpider(scrapy.Spider):
    name = "greyhound_ca"
    item_attributes = {"brand": "Greyhound"}
    allowed_domains = ["bustracker.greyhound.ca"]
    start_urls = [
        "https://bustracker.greyhound.ca/stop-finder/",
    ]

    def parse(self, response):
        locations_data = response.xpath(
            '//script[contains(.,"stopArray")]'
        ).extract_first()
        locations = re.findall(
            r"stopArray.push\((.*?)\);", locations_data, re.MULTILINE | re.DOTALL
        )
        for location in locations:
            location_info = json.loads(location)
            match = re.search(r":\s*(.+),\s(\w+)\s(\w+)", location_info["name"])
            if match:
                street_address, region, postcode = match.groups()
            else:  # no address information available
                street_address, region, postcode = [""] * 3

            website_url = (
                "bustracker.greyhound.ca/stops/"
                + location_info["id"]
                + "/"
                + location_info["linkName"]
            )

            properties = {
                "ref": location_info["id"],
                "name": location_info["shortName"],
                "addr_full": street_address,
                "city": location_info["place"],
                "state": region,
                "postcode": postcode,
                "lat": location_info["stopLatitude"],
                "lon": location_info["stopLongitude"],
                "website": website_url,
            }

            yield GeojsonPointItem(**properties)
