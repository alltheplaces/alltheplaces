# -*- coding: utf-8 -*-
import scrapy
from locations.items import GeojsonPointItem

countries = ['england', 'uk', 'ireland', 'scotland']

formdata = {'sFormName': 'storeFinder',
                'storeFind': 'true',
                'subaction': 'stores_map',
                'sStoreKeywordHidden':'england', # Previous search. The choice of england was arbitrary 
                'sStoreGeo': '',          # Appears to not be used
                'sStoreKeyword': ''}      # Search term 

headers = {'Referer': 'https://www.pcworld.co.uk/gbuk/s/find-a-store.html', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64…) Gecko/20100101 Firefox/57.0'}

class CurrysPcWorldSpider(scrapy.Spider):
    name = "currys"
    allowed_domains = ["https://www.currys.co.uk"] # Change if using PC World 
    # start_urls = ('https://www.currys.co.uk/gbuk/s/find-a-store.html')
    search_url = 'https://www.pcworld.co.uk/gbuk/s/find-a-store.html'
    url = 'https://www.pcworld.co.uk/gbuk/s/3100/find-a-store.html' # response.xpath('//li//@data-location').extract()

    def start_requests(self):
        search_url = 'https://www.pcworld.co.uk/gbuk/s/find-a-store.html'
        for country in countries:
            formdata['sStoreKeyword'] = country
            request = scrapy.FormRequest(search_url, formdata=formdata, callback=self.parse)
            request.meta['country'] = country
            yield request

    def parse(self, response):
        stores = response.xpath('//ul[@class = "borderdList storesList"]//li')

        for store in stores: 
            latitude, longitude = store.xpath('@data-location').extract_first().split()
            address = store.css('div[class="address bsp"]').extract_first()
            address = address.split(sep='\n') # Separating the data 
            address = [i.strip() for i in address] # Lots of whitespace in the websites' text. Removing.
            street_address = address[2]
            city, postal_area, postal_district = address[3].split() # Only relevant section 
            postal_code = ''.join([postal_area, postal_district])   # Postal area + postal district = postal_code
            
            yield GeojsonPointItem(        
                lat = latitude,
                lon = longitude,
                addr_full = street_address,
                city = city,
                country = response.meta['country'])
