# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Fedex_officeSpider(scrapy.Spider):
    name = "fedex_office"
    allowed_domains = []
    start_urls = [
        '',
    ]

    def parse(self, response):
        pass
