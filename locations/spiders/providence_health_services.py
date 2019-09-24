# -*- coding: utf-8 -*-
import json
import re
import scrapy
from locations.items import GeojsonPointItem
from locations.hours import OpeningHours


class Providence_health_servicesSpider(scrapy.Spider):
    name = "providence_health_services"
    allowed_domains = ["providence.org"]

    def start_requests(self):

        ll_urls = ['https://california.providence.org/locations/list-view/',
                   'https://alaska.providence.org/locations/list-view/',
                   'https://oregon.providence.org/location-directory/list-view/'
                   ]

        for url in ll_urls:
            yield scrapy.Request(url, callback=self.parse_ll)

        mp_urls = ['https://montana.providence.org/locations-directory/list-view/',
                   'https://washington.providence.org/locations-directory/search-results/'
                   ]

        for url in mp_urls:
            yield scrapy.Request(url, callback=self.mp_page)

    def ll_page(self, response):
        pages = response.xpath(
            '//*[@id="psjh_body_1_psjh_twocol_celltwo_0_locationsListing_locationsRepeater_headerPagingContainer" ]/a/@href').extract()
        update = pages[-1]
        update = update[:-1] + "1"
        pages.pop()
        pages.append(update)
        for page in pages:
            yield scrapy.Request(response.urljoin(page), callback=self.parse_mp)

    def parse_ll(self, response):
        script = " ".join(response.xpath('//script/text()').extract())
        data = re.search(r'locationsList\s=\s\'(.*?)\'', script).groups()[0]
        data = json.loads(data)

        for place in data:
            for x in place["Locations"]:
                try:
                    street = re.search('\s*(.*)(?=<)', x["Address"]).groups()[0]
                    properties = {
                        'name': x["Name"],
                        'ref': x["Name"] + x["Maps"],
                        'addr_full': street.replace("<br/>", ", "),
                        'city': re.search('(?<=>)\s*([\sA-Za-z]*)(?=,\s*[A-Z]{2}\s*[0-9]{5})', x["Address"]).groups()[
                            0],
                        'state': re.search('>\D*,\s*(.[A-Z]{2})\s*[0-9]{5}', x["Address"]).groups()[0],
                        'postcode': re.search('>\D*,.[A-Z]{2} \s*(\d{5})', x["Address"])[1],
                        'country': "US",
                        'phone': x["PhoneNumber"],
                        'website': x["Maps"],
                        'lat': place["Latitude"],
                        'lon': place["Longitude"],
                    }

                    yield GeojsonPointItem(**properties)
                ## There is one record in Alaska that is missing ["Address"]
                except:
                    pass

    def mp_page(self, response):
        pages = response.xpath(
            '//*[@id="psjh_body_1_psjh_twocol_celltwo_0_locationsListing_locationsRepeater_headerPagingContainer" ]/a/@href').extract()
        update = pages[-1]
        update = update[:-1] + "1"
        pages.pop()
        pages.append(update)
        for page in pages:
            yield scrapy.Request(response.urljoin(page), callback=self.parse_mp)

    def parse_mp(self, response):
        script = response.xpath('//*[@id="mapPoints"]/@value').extract()
        data = json.loads(script[0])

        for place in data:
            coords = place["mapPointLocation"].split(",")

            properties = {
                'name': place["name"],
                'ref': place["name"] + place["moreInfoUrl"],
                'addr_full': place["addressLineOne"],
                'city': place["city"],
                'state': place["state"],
                'postcode': place["postalCode"],
                'country': "US",
                'website': place["moreInfoUrl"],
                'lat': coords[0],
                'lon': coords[1],
            }

            yield GeojsonPointItem(**properties)
