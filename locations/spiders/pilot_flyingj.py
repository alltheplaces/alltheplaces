import csv

import scrapy
from locations.items import GeojsonPointItem


class PilotFlyingJSpider(scrapy.Spider):
    name = "pilot_flyingj"
    item_attributes = {'brand': "Pilot Flying J", 'brand_wikidata': "Q1434601"}
    download_delay = 0.3
    allowed_domains = [
        "pilotflyingj.com",
    ]

    start_urls = [
        'https://pilotflyingj.com/umbraco/surface/storelocations/download?Format=csv&PageSize=1000&PageNumber=1'
    ]

    def parse(self, response):
        for store in csv.DictReader(response.body_as_unicode().splitlines()):
            yield GeojsonPointItem(
                lat=store['Latitude'],
                lon=store['Longitude'],
                name=store['Name'],
                addr_full=store['Address'],
                city=store['City'],
                state=store['State/Province'],
                postcode=store['Zip'],
                country=store['Country'],
                phone=store['Phone'],
                ref=store['Store#'],
                extras={
                    'amenity:fuel': True,
                    'fax': store['Fax'],
                    'fuel:diesel': True,
                    'fuel:HGV_diesel': True,
                    'hgv': True,
                },
                **self.brand_info(store['Name'])
            )

    def brand_info(self, name):
        if 'Pilot' in name:
            return {
                'brand': 'Pilot',
                'brand_wikidata': 'Q7194412'
            }
        elif 'Flying J' in name:
            return {
                'brand': 'Flying J',
                'brand_wikidata': 'Q16974822'
            }
        else:
            return {
                'brand': name
            }
