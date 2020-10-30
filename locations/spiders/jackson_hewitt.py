# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Jackson_hewittSpider(scrapy.Spider):
    name = "jackson_hewitt"
    allowed_domains = []
    start_urls = [
        '',
    ]

    def parse(self, response):
        pass
