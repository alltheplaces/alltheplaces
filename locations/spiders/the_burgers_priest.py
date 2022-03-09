# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class TheBurgersPriestSpider(scrapy.Spider):
    name = "the_burgers_priest"
    item_attributes = {"brand": "The Burger's Priest"}
    allowed_domains = ["theburgerspriest.com"]
    start_urls = [
        "https://theburgerspriest.com/find-a-location/",
    ]

    def parse(self, response):
        data = response.xpath(
            '//script[contains(text(),"locations")]/text()'
        ).extract_first()

        ## Fix lots of formatting issues
        json_data = re.sub(r"var images\s=\s((?s).*?)var locations = ", "", data)
        json_data = re.sub(r'"photo"\s:\s((?s).*?),', "", json_data)
        json_data = re.sub(r'"hours"\s:\s((?s).*?)],', '"hours" : []', json_data)
        json_data = re.sub(r'"description"\s:\s((?s).*?)",', "", json_data)
        json_data = json_data.replace(";", "")
        json_data = json_data[:-12]
        json_data = json_data + "]}"

        places = json.loads(json_data)

        for place in places["features"]:
            try:
                ref = re.search(r".com\/(.*)", place["properties"]["url"]).groups()[0]
            except:
                ref = place["properties"]["name"]

            properties = {
                "ref": ref,
                "name": place["properties"]["name"],
                "addr_full": place["properties"]["address"],
                "city": place["properties"]["city"],
                "state": place["properties"]["provShort"],
                "country": "CA",
                "lat": place["geometry"]["coordinates"][1],
                "lon": place["geometry"]["coordinates"][0],
                "phone": place["properties"]["phone"],
                "website": place["properties"]["url"],
            }

            yield GeojsonPointItem(**properties)
