# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Primrose_schoolsSpider(scrapy.Spider):
    name = "primrose_schools"
    item_attributes = {'brand': ''}
    allowed_domains = []
    start_urls = [
        '',
    ]

    def parse(self, response):
        pass
