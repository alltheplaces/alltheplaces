# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class AmericanCasisoGuideSpider(scrapy.Spider):
    name = "american_casiso_guide"
    allowed_domains = ['americancasinoguide.com']

    def start_requests(self):
        # states =["alabama","alaska","arizona","arkansas","california","colorado",
        #       "connecticut","delaware","florida","georgia","hawaii","idaho","illinois",
        #       "indiana","iowa","kansas","kentucky","louisiana","maine","maryland",
        #       "massachusetts","michigan","minnesota","mississippi","missouri","montana",
        #       "nebraska","nevada","new hampshire","new jersey","new mexico","new york",
        #       "north carolina","north dakota","ohio","oklahoma","oregon","pennsylvania",
        #       "rhode island","south carolina","south dakota","tennessee","texas","utah",
        #       "vermont","virginia","washington","west virginia","wisconsin","wyoming"]

        states = ["alabama"]

        base_url = 'https://www.americancasinoguide.com/'

        for state in states:
            yield scrapy.Request(url=base_url.urljoin(state), callback=self.parse_states)

    def parse_states(self, response):
        casino_urls = response.xpath('//*[@class="col-sm-2 col-xs-4"]/a/@href').extract()

        for casino in casino_urls:
            print(casino)
