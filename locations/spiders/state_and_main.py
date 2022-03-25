# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class StateAndMainSpider(scrapy.Spider):
    name = "state_and_main"
    item_attributes = {"brand": "State & Main"}
    allowed_domains = ["stateandmain.ca"]
    start_urls = [
        "https://www.stateandmain.ca/",
    ]

    def parse(self, response):
        data = response.xpath(
            '//script[contains(text(),"ojlocations")]/text()'
        ).extract_first()

        ## Fix lots of formatting issues
        json_data = data.replace("var ojlocations = ", "")
        json_data = re.sub(r'"hours":\s{((?s).*?)},', "", json_data)
        json_data = re.sub(
            r'"holidayHours":\s{((?s).*?)},', '"holidayHours": {}', json_data
        )
        json_data = re.sub(r"var currentLocation\s=\s{((?s).*?)};", "", json_data)
        json_data = json_data.replace(";", "")
        json_data = json_data[:-8]
        json_data = json_data + "}"

        places = json.loads(json_data)

        for place in places:
            try:
                coords = places[place]["geo"]
                lat, lng = coords.split(",")

                properties = {
                    "ref": place,
                    "name": places[place]["Title"],
                    "addr_full": places[place]["streetAddress"],
                    "city": places[place]["city"],
                    "state": places[place]["province"],
                    "postcode": places[place]["postalCode"],
                    "country": "CA",
                    "lat": lat,
                    "lon": lng,
                    "phone": places[place]["telephone"],
                }

                yield GeojsonPointItem(**properties)
            except:
                pass
