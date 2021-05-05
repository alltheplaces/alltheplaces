# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class ThalesFrSpider(scrapy.Spider):
    name = "thales_fr"
    item_attributes = {'brand': "Thales"}
    allowed_domains = ['google.com']
    start_urls = [
        'https://www.google.com/maps/d/u/0/embed?mid=1yA7rNTU7COi4W6wrLiZ8Ro0Kem8&ll=48.40753354596532%2C-4.58267066250005&z=6',
    ]

    def parse(self, response):
        data = response.xpath(
            '//script[@type="text/javascript" and contains(text(), "_pageData")]/text()').extract_first()

        places = re.findall(r"Entity(.*?)KO", data)

        for place in places:
            addr = re.search(r'Address\\",\[\\"(.*?)\\"\]', place).group(1)
            if "France" not in addr:
                pass
            else:
                addr_split = addr.split(",")
                if len(addr_split) == 4:
                    street = addr_split[0] + addr_split[1]
                    postal = re.search(r'\d{5}', addr_split[2]).group(0)
                else:
                    street = addr_split[0]
                    postal = re.search(r'\d{5}', addr_split[1]).group(0)
                    locality = addr_split[1].replace(postal, "").strip()

            properties = {
                'ref': re.search(r'null,(\d*?)\]', place).group(1),
                'name': re.search(r'\[\\"(.*?)\\"\]', place).group(1).replace("\\\\u0026", "&"),
                'addr_full': street,
                'city': locality,
                'postcode': postal,
                'country': 'FR',
                'lat': re.search(r'Latitude\\",\[\\"(.*?)\\', place).group(1),
                'lon': re.search(r'Longitude\\",\[\\"(.*?)\\', place).group(1)
            }

            yield GeojsonPointItem(**properties)
