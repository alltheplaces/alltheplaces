# -*- coding: utf-8 -*-
import scrapy
import re
import json

from locations.items import GeojsonPointItem

class AldiUKSpider(scrapy.Spider):
    name = "aldiuk"
    chain_name = "Aldi"
    allowed_domains = ['www.aldi.co.uk']
    start_urls = (
        'https://www.aldi.co.uk/sitemap/store',
    )

    def parse(self, response):
        response.selector.remove_namespaces()
        city_urls = response.xpath('//url/loc/text()').extract()
        for path in city_urls:
            yield scrapy.Request(
                path.strip(),
                callback=self.parse_store,
            )
        else:
            pass

    def parse_store(self, response):
        json_data = response.xpath('//script[@type="text/javascript"]/text()').extract_first().replace('\n','').replace('\t','').split('.push(')[1].rstrip(')')
        data = json.loads(json_data)
        geojson_data = response.xpath('//script[@class="js-store-finder-initial-state"][@type="application/json"]/text()').extract_first()
        geodata = json.loads(geojson_data)

        properties = {
        'name': data['seoData']['name'],
        'ref': data['seoData']['name'],
        'addr_full': data['seoData']['address']['streetAddress'],
        'city': data['seoData']['address']['addressLocality'],
        'postcode': data['seoData']['address']['postalCode'],
        'country': data['seoData']['address']['addressCountry'],
        'website': response.request.url,
        'opening_hours': str(data['seoData']['openingHours']).replace('[','').replace(']','').replace("'",''),
        'lat': float(geodata['store']['latlng']['lat']),
        'lon': float(geodata['store']['latlng']['lng']),
        }

        yield GeojsonPointItem(**properties)
