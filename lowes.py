# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem
import json 
from urllib.parse import urlencode

class LowesSpider(scrapy.Spider):
    """" This spider scrapes Lowes store locations """
    name = "lowes"
    allowed_domains = ["https://www.lowes.com"]
    start_urls = ('https://www.lowes.com/store/')

    def zip_codes(self):
        """ Generates all possible zip codes as strings """
        import itertools as it

        for i in it.product('0123456789', repeat=5): # Create all possible 5 digit zip codes as tuples
            yield ''.join(i)                         # Join together into a zip code 
            
    def start_requests(self):
        base_url = 'https://www.lowes.com/wcs/resources/store/10151/storelocation/v1_0?%s'
        
        headers = {'Accept-Encoding': 'gzip, deflate, br', 'Accept-Language': 'en-US,en;q=0.5',
                   'Authorization': 'Basic QWRvYmU6ZW9pdWV3ZjA5ZmV3bw==',
                    'Connection': 'keep-alive', 'Cookie': 'stop_mobi=yes; AKA_A2=1; _abck…-mPZl0ml9x:1bhcvvuj1; sn=3240',
                    'DNT': '1', 'Host': 'www.lowes.com', 'Referer': 'https://www.lowes.com/store/',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64…) Gecko/20100101 Firefox/57.0', 'X-Requested-With': 'XMLHttpRequest'}

        for zip_code in self.zip_codes():
            params = urlencode({'maxResults': 30, 'query': zip_code})
            search_url = base_url % params
            yield scrapy.Request(search_url, headers=headers, callback=self.parse) 

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data['storeLocation']

        for store in stores:
            yield GeojsonPointItem(
                lat=store['latitude'],
                lon=store['longitude'],
                addr_full=store["address1"],
                city=store["city"],
                state=store["state"]
                )
        
