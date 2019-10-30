# -*- coding: utf-8 -*-
import json
import re

import scrapy

from locations.items import GeojsonPointItem
from locations.hours import OpeningHours

BASE_URL = 'https://www.goodwill.org/getLocations.php'


class GoodwillSpider(scrapy.Spider):
    name = "goodwill"
    allowed_domains = ['www.goodwill.org']
    download_delay = 0.2

    def start_requests(self):
        url = BASE_URL
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        # Unable to find a way to specify a search radius
        # Appears to use a set search radius somewhere > 25mi, using 25mi to be safe
        form_data = {
            'lat': '{}'.format('35.844116'),
            'lng': '{]'.format('-86.396779'),
            'cats': '3,1,2,4,5'  # Includes donation sites
        }

        yield scrapy.http.FormRequest(url=url, method='POST', formdata=form_data, headers=headers,
                                      callback=self.parse)

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        pass
