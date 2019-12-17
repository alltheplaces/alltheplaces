# -*- coding: utf-8 -*-
import scrapy
import json
import re
import logging

from locations.items import GeojsonPointItem

class PigglyWigglySpider(scrapy.Spider):
    ''' This spider scrapes from two different places, an api which has their stores in Wisconsin
        and Illinois, and a page which has all of their other stores. Cookies are used for the
        api request.
    '''
    name = "pigglywiggly"
    item_attributes = { 'brand': "Piggly Wiggly" }
    allowed_domains = ["pigglywiggly.com"]

    def start_requests(self):
        url = 'https://www.shopthepig.com/api/m_store_location'
        headers = {
            'x-newrelic-id': 'XQYBWFVVGwAEVFNRBQcP',
            'accept-encoding': 'gzip, deflate, br',
            'x-csrf-token': 'eF2m10r8n51nsRgBSv1xSvhAGtCo8E84BExlmn54Vvc',
            'accept-language': 'en-US,en;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            'accept': 'application/json, text/plain, */*',
            'referer': 'https://www.shopthepig.com/stores',
        }
        cookies = {
            '__cfduid': 'db0a53231376d78a40dd7fd728fa896f51512948321',
            'SESSb159e7a0d4a6fad9ba3abc7fadef99ec': 'h3o7xcjnfcERSRrqJVh0soQdUI5IFIBDIQlytOZkhIU',
            'XSRF-TOKEN': 'eF2m10r8n51nsRgBSv1xSvhAGtCo8E84BExlmn54Vvc',
            'has_js': 1,
        }

        yield scrapy.http.FormRequest(
            url=url, headers=headers, callback=self.parse_wi, cookies=cookies
        )

        yield scrapy.Request(
            'https://www.pigglywiggly.com/store-locations',
            callback=self.parse_nonwi,
        )

    def parse_wi(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data['stores']
        for store in stores:
            unp = {
                'ref': store['storeID'],
                'name': store['storeName'],
                'addr_full': store['normalized_address'],
                'city': store['normalized_city'],
                'state': store['normalized_state'],
                'postcode': store['normalized_zip'],
                'lat': store['latitude'],
                'lon': store['longitude'],
                'phone': store['phone']
            }
            properties = {}
            for key in unp:
                if unp[key]: properties[key] = unp[key]

            yield GeojsonPointItem(**properties)

    def parse_nonwi(self, response):
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
