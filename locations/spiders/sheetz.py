import json
import re
import scrapy
from locations.items import GeojsonPointItem


class SheetzSpider(scrapy.Spider):
    name = "sheetz"
    brand = "Sheetz"
    allowed_domains = ["orderz.sheetz.com"]
    start_urls = (
        "https://orderz.sheetz.com/sas/location?address=90210&fuelPrice=true&page=0&radius=1500&size=10000",
    )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())
        stores = data['locations']
        hourdict = {}
        for store in stores:
            properties = {
                'addr_full': store['address'],
                'city': store['city'],
                'state': store['state'],
                'postcode': store['zip'],
                'ref': store['storeNumber'],
                'website': 'https://orderz.sheetz.com/#/main/location/store/'+store['storeNumber'],
                'lat': float(store['latitude']),
                'lon': float(store['longitude']),
            }

            yield GeojsonPointItem(**properties)