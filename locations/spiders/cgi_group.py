# -*- coding: utf-8 -*-
import re
import scrapy
import json

from locations.items import GeojsonPointItem


class CGISpider(scrapy.Spider):
    name = "cgi_group"
    allowed_domains = ["cgi.com"]
    download_delay = 0.5
    start_urls = (
        'https://www.cgi.com/en/offices?field_address_country_code=All&field_address_administrative_area=All&field_address_locality=All',
    )

    def checklist(self, mylist):
        try:
            string = mylist[0]
            return string
        except IndexError:
            return None

    def parse_country(self, response):
        data = json.loads(response.xpath('//script[@type="application/json"]/text()').extract_first())

        offices = data['geofield_google_map']['geofield-map-view-newoffices-block-1']['data']['features']

        for office in offices:

            properties = {
                'name': re.findall('(?<=<span>).*?(?=<)', office['properties']['description'])[0],
                'addr_full': re.findall('(?<=-line1">).*?(?=<)', office['properties']['description'])[0],
                'city': re.findall('(?<=locality">).*?(?=<)', office['properties']['description'])[0],
                'state': self.checklist(re.findall('(?<=administrative-area">).*?(?=<)',
                                                   office['properties']['description'])),
                'postcode': self.checklist(re.findall('(?<=postal-code">).*?(?=<)',
                                                      office['properties']['description'])),
                'lat': float(office['geometry']['coordinates'][1]),
                'lon': float(office['geometry']['coordinates'][0]),
                'country': re.findall('(?<=country">).*?(?=<)', office['properties']['description'])[0],
                'ref': re.findall('(?<=<span>).*?(?=<)', office['properties']['description'])[0],
                'website': response.url
            }

            yield GeojsonPointItem(**properties)

    def parse(self, response):
        countries = response.xpath('//select[@data-drupal-selector="edit-field-address-country-code"]/option').extract()
        for country in countries:
            country = re.findall(r'"([^"]*)"', country)
            if country[0] != "All":
                url = 'https://www.cgi.com/en/offices?field_address_country_code={country}&field_address_administrative_area=All&field_address_locality=All'.format(country=country[0])
                yield scrapy.Request(url, callback=self.parse_country)
