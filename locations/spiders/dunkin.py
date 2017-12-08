# -*- coding: utf-8 -*-
import scrapy
import re
from locations.items import GeojsonPointItem
import json

class DunkinSpider(scrapy.Spider):
    name = "dunkindonuts"
    allowed_domains = ["dunkindonuts.com","mapquestapi.com"]

    # Choosing key hub at geographic extremes of the US in order to get full coverage in the location search
    search_hubs = ['washington+dc','los+angeles','miami','boston','chicago']

    start_urls = ['https://www.mapquestapi.com/search/v2/radius?callback=' \
                  'jQuery111205309142260006529_1512766475273&key=Gmjtd|lu6t2l' \
                  'uan5%2C72%3Do5-larsq&origin=' + i + '&units=m&maxMatches=4000' \
                                                       '&radius=3000&hostedData=' \
                                                       'mqap.33454_DunkinDonuts&ambi' \
                                                       'guities=ignore&_=1512766475279' for i in search_hubs]


    def parse(self,response):

        query_data = response.body.decode('utf-8')
        pure_query = re.search("\(((.*)\);)",query_data).group(2)
        jdata = json.loads(pure_query)

        for i in jdata['searchResults']:


            properties = {

                'ref': i['key'],
                'country': i['fields']['country'],
                'state': i['fields']['state'],
                'city': i['fields']['city'],
                'lat': i['fields']['mqap_geography']['latLng']['lat'],
                'lon': i['fields']['mqap_geography']['latLng']['lng'],
                'phone': i['fields']['phonenumber'],
                'addr_full': i['fields']['address'],
                'postcode': i['fields']['postal'],


            }


            yield GeojsonPointItem(**properties)
