# -*- coding: utf-8 -*-
import itertools
import re

import scrapy

from locations.items import GeojsonPointItem


class VitalantSpider(scrapy.Spider):
    name = "vitalant"
    item_attributes = {"brand": "Vitalant", "brand_wikidata": "Q7887528"}
    allowed_domains = ["vitalant.org"]
    start_urls = ("https://vitalant.org/Donate/Locations",)

    def parse(self, response):
        [script] = response.xpath(
            '//script/text()[contains(., "BasicGoogleMaps = ")]'
        ).extract()
        marker_lines = []
        location_lines = []
        for line in script.splitlines():
            match = re.search(r"<div.*/div>", line)
            if match is not None:
                marker_lines.append(match[0])
            elif "addGoogleMarker" in line:
                location_lines.append(line)

        for marker, location in itertools.zip_longest(marker_lines, location_lines):
            selector = scrapy.Selector(text=marker)
            name, *addrs, addr2 = (
                s.strip()
                for s in selector.xpath("//b/text()[normalize-space()]").extract()
            )
            city, state, postcode = re.search("(.*), (.*) (.*)", addr2).groups()
            website = selector.xpath("//@href").extract_first().strip(r"\"")
            lat, lon = location.split(", ")[1:3]
            ref = re.search(r"BasicGoogleMaps\[(\d+)\]", location)[1]
            properties = {
                "ref": ref,
                "lat": lat,
                "lon": lon,
                "website": response.urljoin(website),
                "name": name,
                "addr_full": ", ".join(addrs),
                "city": city,
                "state": state,
                "postcode": postcode,
            }
            yield GeojsonPointItem(**properties)
