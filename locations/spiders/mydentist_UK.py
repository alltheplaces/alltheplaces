# -*- coding: utf-8 -*-
import re

import scrapy

from locations.items import GeojsonPointItem

class MyDentistSpider(scrapy.Spider):
    #download_delay = 0.2
    name = "my_dentist"
    item_attributes = {'brand': "MY DENTIST", 'brand_wikidata': "Q65118035"}
    allowed_domains = ["mydentist.co.uk"]

    start_urls = ([
        'https://www.mydentist.co.uk/'
    ])

    def parse(self, response):
        with open('./locations/searchable_points/eu_centroids_120km_radius_country.csv') as points:
            next(points)
            for point in points:
                row = point.replace('\n', '').split(',')
                lati = row[1]
                long = row[2]
                country = row[3]
                print(row)
                if country == "UK":
                    print(country)
                    searchurl = 'https://www.mydentist.co.uk/Workflow/DentistSearch/_SearchResult?searchData=&clientLat={la}&clientLng={lo}&searchoption=private%2Cnhs%2Cortho%2C&numberOfResults=1000&widgetName=DentistSearch&quickContronFormOptions=&isquickContactForm=False&_=1632838745154'.format(la=lati, lo=long)
                    yield scrapy.Request(response.urljoin(searchurl), callback=self.parse_search)

    def parse_search(self, response):
        print('Searching....')
        stores = response.xpath('//div[@class="practice-details"]').extract()
        count = 0
        for i in stores:
            count = count + 1
            store = re.sub(' +', ' ', i)
            try:
                address = re.search('r>\r\n ([^;]*) <br>', store).group(1).split(', ')[0]
                city = re.search('r>\r\n ([^;]*) <br>', store).group(1).split(', ')[1]
                zip = re.search('r>\r\n ([^;]*) <br>', store).group(1).split(', ')[2]
                phone = re.search('tel">([^;]*)</a>\r\n', store).group(1)
                lat = float(re.search('latitude="([^;]*)" data-lon', store).group(1))
                lon = float(re.search('longitude="([^;]*)">\r\n <strong', store).group(1))
                ref = re.search('data-title="([^;]*)" data-lati', store).group(1)

                properties = {
                    'ref': ref,
                    'name': 'MyDentist',
                    'addr_full': address,
                    'city': city,
                    'postcode': zip,
                    'country': 'UK',
                    'phone': phone,
                    'lat': lat,
                    'lon': lon
                }

                yield GeojsonPointItem(**properties)
            except:
                print(store)
                pass