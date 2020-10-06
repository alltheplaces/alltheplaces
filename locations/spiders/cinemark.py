# -*- coding: utf-8 -*-
import json
import csv

import scrapy

from locations.items import GeojsonPointItem

class CinemarkSpider(scrapy.Spider):
    name = "cinemark"
    item_attributes = {'brand': "Cinemark"}
    allowed_domains = ["cinemark.com"]
    download_delay = 2


    def start_requests(self):
        url = "https://www.cinemark.com/theatres/{zipcode}"

        with open('./locations/searchable_points/us_zcta.csv') as zipcodes:
            # reader = csv.reader(zipcodes)
            next(zipcodes)
            for zipcode in zipcodes:
                yield scrapy.Request(
                    url = url.format(zipcode = zipcode.replace('"', '')),
                    callback=self.parse
                )
                break

    def parse(self, response):
        data = response.xpath('//script[@type="application/ld+json"]//text()').extract_first()
        data = json.loads(data.split(';')[0]) # remove trailing ';'
        for store in data:
            properties = {
                'ref': store["@id"],
                'name': store["name"],
                'addr_full': store["address"][0]["streetAddress"],
                'city': store["address"][0]["addressLocality"],
                'postcode': store["address"][0]["postalCode"],
                'country': "US",
                'phone': store.get("telephone"),
            }

            yield GeojsonPointItem(**properties)
