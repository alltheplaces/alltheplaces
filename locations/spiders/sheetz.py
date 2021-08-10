import json
import re
import scrapy
from locations.items import GeojsonPointItem


class SheetzSpider(scrapy.Spider):
    name = "sheetz"
    item_attributes = {'brand': "Sheetz"}
    allowed_domains = ["orderz.sheetz.com"]
    start_urls = (
        "https://orderz.sheetz.com/sas/store",
    )

    def parse(self, response):
        stores = json.loads(response.body_as_unicode())

        for store in stores:
            properties = {
                'addr_full': store['address'],
                'city': store['city'],
                'state': store['state'],
                'postcode': store['zip'],
                'ref': store['storeNumber'],
                'phone': store.get('phone'),
                'website': 'https://orderz.sheetz.com/#/main/location/store/'+store['storeNumber'],
                'lat': float(store['latitude']),
                'lon': float(store['longitude']),
                'opening_hours': '24/7' if store['open24x7'] else None,
                'extras': {
                    'amenity:chargingstation': store['evCharger'],
                    'amenity:fuel': True,
                    'atm': store['atm'],
                    'car_wash': store['carWash'],
                    'fax': store['fax'] if 'fax' in store else None,
                    'fuel:diesel': store['diesel'],
                    'fuel:e15': store['e15'],
                    'fuel:e85': store['e85'],
                    'fuel:kerosene': store['kerosene'],
                    'fuel:propane': store['propane'],
                }
            }

            yield GeojsonPointItem(**properties)
