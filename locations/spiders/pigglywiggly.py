# -*- coding: utf-8 -*-
import scrapy
import json
import re
import logging

from locations.items import GeojsonPointItem

# Currently, this spider only gathers location data from their non - wisconsin and illinois stores.
# Gathering data from those locations involves sending a request to an api that is specifically
# for their stores in those two states.
class PigglyWigglySpider(scrapy.Spider):
    name = "pigglywiggly"
    allowed_domains = ["pigglywiggly.com"]
    
    start_urls = (
        'https://www.pigglywiggly.com/store-locations',
    )

    # NOTE: this buildRequest function (and parse_wi) don't work, their api returns 401.
    # If they worked, these functions would gather location data from their wisconsin and illinois stores.
    def buildRequest(self):
        url = 'https://www.shopthepig.com/api/m_store_location'
        headers = {
            'x-newrelic-id': 'XQYBWFVVGwAEVFNRBQcP',
            'accept-encoding': 'gzip, deflate, br',
            'x-csrf-token': 'eF2m10r8n51nsRgBSv1xSvhAGtCo8E84BExlmn54Vvc',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            'accept': 'application/json, text/plain, */*',
            'referer': 'https://www.shopthepig.com/stores',
            'authority': 'www.shopthepig.com',
            'cookie': '__cfduid=d5633fa71f6dd159d419cbb684774a76d1512714801; SESSb159e7a0d4a6fad9ba3abc7fadef99ec=h3o7xcjnfcERSRrqJVh0soQdUI5IFIBDIQlytOZkhIU; XSRF-TOKEN=eF2m10r8n51nsRgBSv1xSvhAGtCo8E84BExlmn54Vvc;',
        }

        yield scrapy.http.FormRequest(
            url=url, method='GET',
            headers=headers, callback=self.parse_wi
        )

    def parse_wi(self, response):
        logging.info(response.body_as_unicode())

    def parse(self, response):
        for state_url in response.xpath('//div[@class="views-field-province-1"]/span[@class="field-content"]/a/@href').extract():
            yield scrapy.Request(
                response.urljoin(state_url),
                callback=self.parse_state,
            )

    def parse_state(self, response):
        for location in response.xpath('//li[contains(@class, "views-row")]'):
            unp = {
                'addr_full': location.xpath('.//div[@class="street-address"]/text()').extract_first(),
                'city': location.xpath('.//span[@class="locality"]/text()').extract_first(),
                'state': location.xpath('.//span[@class="region"]/text()').extract_first(),
                'postcode': location.xpath('.//span[@class="postal-code"]/text()').extract_first(),
                'phone': location.xpath('.//label[@class="views-label-field-phone-value"]/following-sibling::span[1]/text()').extract_first(),
                'website': location.xpath('.//label[@class="views-label-field-website-value"]/following-sibling::span[1]/a/@href').extract_first(),
            }
            if unp['website']:
                if 'google' in unp['website']:
                    unp['website'] = None
                    
            if unp['phone']:
                unp['phone'] = unp['phone'].replace('.', '-')

            properties = {}
            for key in unp:
                if unp[key]:
                    properties[key] = unp[key].strip()
            ref = ''
            if 'addr_full' in properties: ref += properties['addr_full'] 
            if 'phone' in properties: ref += properties['phone'] 
            properties['ref'] = ref

            yield GeojsonPointItem(**properties)

