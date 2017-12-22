# -*- coding: utf-8 -*-
import scrapy
from scrapy.linkextractors import LinkExtractor
from locations.items import GeojsonPointItem
import json
from w3lib.html import remove_tags

STATES = ["al", "ak", "az", "ar", "ca", "co", "ct", "dc", "de", "fl", "ga", 
          "hi", "id", "il", "in", "ia", "ks", "ky", "la", "me", "md", 
          "ma", "mi", "mn", "ms", "mo", "mt", "ne", "nv", "nh", "nj", 
          "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa", "ri", "sc", 
          "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy"] # U.S States

HEADERS = {'Referer': 'https://stores.joann.com'}

class JoAnnFabricsSpider(scrapy.Spider):
    name = 'joann_fabrics'
    allowed_domains = ['www.joann.com','stores.joann.com']

    def start_requests(self):
        """ Yields a scrapy.Request object for each state in the USA """ 
        base_url = 'https://stores.joann.com/{}'
        
        for state in STATES:
            state_url = base_url.format(state)
            request = scrapy.Request(state_url, callback=self.parse_state, headers=HEADERS)
            request.meta['state'] = state
            yield request
    
    def parse_state(self, response):
        """ Yields a scrapy.Request object for each city with a store in the state """
        state_url = 'stores.joann.com/{}*'.format(response.meta['state'])
        extractor = LinkExtractor(allow=state_url)

        for link in extractor.extract_links(response):
            yield scrapy.Request(link.url, callback=self.parse_city, headers=HEADERS)
            
    def parse_city(self, response): # Not getting called  
        """ Extracts the store information for a given city """
        stores = response.xpath('//script[@type = "application/ld+json"]/text()')[1:].extract() # The first result is irrelevent
        
        for store in stores:
            store = remove_tags(store)
            store = json.loads(store)
            yield GeojsonPointItem(
                addr_full = store['address']['streetAddress'],
                country = store['address']['addressCountry'],
                postcode = store['address']['postalCode'],
                state = store['address']['addressRegion'],
                city = store['address']['addressLocality'],
                ref = store['url'],
                phone = store['telephone'],
                name = store['branchOf']['name']
                )
