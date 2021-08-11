# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Ricoh_usSpider(scrapy.Spider):
    name = "ricoh_us"
    allowed_domains = []
    start_urls = [
        '',
    ]

    def parse(self, response):
        pass
