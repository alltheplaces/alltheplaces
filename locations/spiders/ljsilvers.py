# -*- coding: utf-8 -*-
import scrapy
import json
import re

from locations.items import GeojsonPointItem


class LjsilversSpider(scrapy.Spider):
    name = "ljsilvers"
    allowed_domains = ["ljsilvers.com"]
    start_urls = (
        'http://www.ljsilvers.com/locator?postalcode=76010',
    )

    def parse(self, response):
        base_data = re.search('dataout\s--Array\s\((.*)\)\s\s--><style type="text/css">', response.body, re.DOTALL).group(1)
        detail_matches = re.findall('\((.*?)\)', base_data, re.DOTALL)

        for detail_match in detail_matches:
            key_values = re.findall('(.*?)\s=>\s(.*)', detail_match)
            props = {}

            for key_value in key_values:
                key = key_value[0].strip()
                value = key_value[1].strip()

                if key == '[storeID]':
                    props['ref'] = value
                if key == '[address]':
                    props['addr_full'] = value
                if key == '[city]':
                    props['city'] = value
                if key == '[state]':
                    props['state'] = value
                if key == '[zip]':
                    props['postcode'] = value
                if key == '[phone_number]':
                    props['phone'] = value
                if key == '[latitude]':
                    props['lat'] = value
                if key == '[longitude]':
                    props['lon'] = value

            yield GeojsonPointItem(**props)
