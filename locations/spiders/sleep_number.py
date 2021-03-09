# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Sleep_numberSpider(scrapy.Spider):
    name = "sleep_number"
    allowed_domains = []
    start_urls = [
        '',
    ]

    def parse(self, response):
        pass
