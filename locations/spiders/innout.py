# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem

class TemplateSpider(scrapy.Spider):
    name = "innout"

    allowed_domains = ["www.in-n-out.com"]
    start_urls = ['http://locations.in-n-out.com/api/finder/search/?showunopened=false&latitude='
                  '37.751&longitude=-97.822&maxdistance=3050&maxresults=2500']


    def parse(self, response):
        # testing
        response.selector.remove_namespaces()


        cities = response.xpath('//LocationFinderStore/City/text()').extract()
        lats = response.xpath('//LocationFinderStore/Latitude/text()').extract()
        longs = response.xpath('//LocationFinderStore/Longitude/text()').extract()
        snumber = response.xpath('//LocationFinderStore/StoreNumber/text()').extract()
        saddress = response.xpath('//LocationFinderStore/StreetAddress/text()').extract()
        zipcodes = response.xpath('//LocationFinderStore/ZipCode/text()').extract()
        states = response.xpath('//LocationFinderStore/State/text()').extract()
        names = response.xpath('//LocationFinderStore/Name/text()').extract()

        for city,state,lat,lon,sNumb,sAddr,zcode,key in zip(cities, states, lats, longs, snumber,saddress,zipcodes,names):


            properties = {


                'addr_full': sNumb + " " + sAddr,
                'city': city,
                'state': state,
                'postcode': zcode,
                'ref': str(sNumb + key),
                'lon': float(lon),
                'lat': float(lat),



            }

            yield GeojsonPointItem(**properties)




