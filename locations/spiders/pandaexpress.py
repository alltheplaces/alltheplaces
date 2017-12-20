# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import json
from locations.items import GeojsonPointItem


class PandaSpider(scrapy.Spider):
    name = "pandaexpress"
    allowed_domains = ["inkplant.com", "pandaexpress.com"]
    start_urls = ['https://inkplant.com/code/state-latitudes-longitudes']

    def parse(self, response):

        # Get all state names to search for Panda Express
        sname = response.xpath("//tr//td[1]/text()").extract()[1:]
        # Add Puerto Rico
        sname.append("Puerto Rico")

        # Iterate through each state to locate Panda Express Locations
        for state in sname:

            state_url = "https://www.pandaexpress.com/userlocation/searchbyquery?query="+state+\
                        "&limit=1000&hours=true&_=1512680879964"

            # parse and return relevant location information
            yield Request(state_url, callback=self.parseState)

    def parseState(self, response):
        state_data = json.loads(response.body_as_unicode())

        for store in state_data:
            properties = {
                'addr_full': store['Address'],
                'city': store["City"],
                'state': store['State'],
                'postcode': store['Zip'].strip(),
                'ref': store['Id'],
                'lon': float(store['Longitude']),
                'lat': float(store['Latitude']),
                'phone': store['Phone']
            }

            yield GeojsonPointItem(**properties)
