# -*- coding: utf-8 -*-
import scrapy
import json
import urllib

from locations.items import GeojsonPointItem

HEADERS = {'Content-Type': 'application/json'}

BRANDS = {
    'U76': '76',
    'P66': 'Phillips 66',
    'CON': 'Conoco'
}

WIKIBRANDS = {
    'U76': 'Q1658320',
    'P66': 'Q1656230',
    'CON': 'Q1126518'
}


class Phillips66Spider(scrapy.Spider):
    name = "phillips_66_conoco_76"
    allowed_domains = ["spatial.virtualearth.net"]
    download_delay = 0.2

    base_url = "https://spatial.virtualearth.net/REST/v1/data/a1ed23772f5f4994a096eaa782d07cfb/US_BrandedSites/Sites?$filter=(Brand%20eq%20%27P66%27%20OR%20Brand%20Eq%20%27U76%27%20OR%20Brand%20Eq%20%27CON%27)&$format=json&$inlinecount=allpages&$select=*,__Distance&key=AvroZVNGVuRnilfbaoMSyXJhjA36NTNr8jdIufcn1erJ_kJMF5UE33M_ENXxHwTb&$top=250"

    def start_requests(self):
        yield scrapy.Request(self.base_url, callback=self.get_pages)

    def get_pages(self, response):
        result = json.loads(response.body_as_unicode())
        total_count = int(result['d']['__count'])
        offset = 0

        while offset < total_count:
            yield scrapy.Request(self.base_url + f"&$skip={offset}")
            offset += 250

    def parse(self, response):
        result = json.loads(response.body_as_unicode())

        for station in result['d']['results']:
            yield GeojsonPointItem(
                lat=station['Latitude'],
                lon=station['Longitude'],
                name=station['Name'],
                addr_full=station['AddressLine'],
                city=station['Locality'],
                state=station['AdminDistrict'],
                postcode=station['PostalCode'],
                country=station['CountryRegion'],
                phone=station['Phone'],
                ref=station['EntityID'],
                brand=BRANDS[station['Brand']],
                brand_wikidata=WIKIBRANDS[station['Brand']],
                extras={
                    'amenity': 'fuel',
                    'e85': station['e85'],
                    'e66': station['E66'],
                    'diesel': station['Diesel'],
                    'car_wash': station['CarWash'],
                    'convenience_store': station['CStore'],
                    'snacks': station['Snacks'],
                    'atm': station['ATM']
                }
            )
