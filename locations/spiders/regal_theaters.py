# -*- coding: utf-8 -*-
import scrapy
import json
from locations.items import GeojsonPointItem

class RegalTheatersSpider(scrapy.Spider):
    name = 'regal-theaters'
    allowed_domains = ['www.regmovies.com']
    # Send cookies with a location where there aren't any theaters so that
    # response will be a list of theaters.
    cookies = [
      { 'name': 'lat', 'value': 50, 'domain': allowed_domains[0], 'path': '/' },
      { 'name': 'lon', 'value': -117, 'domain': allowed_domains[0], 'path': '/' },
      { 'name': 'locationName', 'value': 'San Diego', 'domain': allowed_domains[0], 'path': '/' }
    ]

    def start_requests(self):
        urls = [
            'https://www.regmovies.com/theaters',
        ]
        for url in urls:
            yield scrapy.Request(url=url, 
                cookies=self.cookies,
                callback=self.parse_theaters)

    def parse_theaters(self, response):
        theaters = response.xpath('//*[contains(@class, "state-venue-list")]/li/a/@href').extract()
        for theater in theaters:
            yield scrapy.Request(response.urljoin(theater), callback=self.parse)
    
    def parse(self, response):
        theater = response.xpath('//script[@type="application/ld+json"]/text()').extract_first()
        theaterJson = json.loads(theater)
        properties = {
          'addr_full': theaterJson['address'],
          'state': theaterJson['address'].split(', ')[-1],
          'website': response.url,
          'ref': response.url.split('/')[-1],
          'lon': theaterJson['geo']['longitude'],
          'lat': theaterJson['geo']['latitude'],
          'extras': { 'name': theaterJson['name'] }
        }
        # A few pages are missing phone numbers.
        if 'telephone' in theaterJson:
            properties['phone'] = theaterJson['telephone']
        yield GeojsonPointItem(**properties)
