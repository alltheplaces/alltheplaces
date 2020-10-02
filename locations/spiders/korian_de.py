# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Korian_deSpider(scrapy.Spider):
    name = "korian_de"
    allowed_domains = []
    start_urls = [
        '',
    ]

    def parse(self, response):
        pass
