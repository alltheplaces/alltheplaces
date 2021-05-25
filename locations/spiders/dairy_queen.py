import scrapy
import re
import json
from locations.items import GeojsonPointItem


class DairyQueenSpider(scrapy.Spider):

    name = "dairyqueen"
    item_attributes = { 'brand': "Dairy Queen", 'brand_wikidata': "Q1141226" }
    allowed_domains = ["www.dairyqueen.com"]
    start_urls = (
        'https://www.dairyqueen.com/en-us/locations/',
    )

    def start_requests(self):
        yield scrapy.Request(
            'https://prod-dairyqueen.dotcmscloud.com/api/es/search',
            method='POST',
            headers={
                'content-type': 'application/json',
                'accept': 'application/json',
                'referer': 'https://www.dairyqueen.com/',
            },
            body='{"size":5000,"query":{"bool":{"must":[{"term":{"contenttype":"locationDetail"}}]}}}}',
        )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data['contentlets']:

            lat, lon = store.get('latlong', ',').split(',', 2)

            properties = {
                'addr_full': store.get('address3'),
                'phone': store.get('phone'),
                'city': store.get('city'),
                'state': store.get('stateProvince'),
                'postcode': store.get('postalCode'),
                'ref': store.get('storeId'),
                'website': 'https://www.dairyqueen.com' + store.get('urlTitle'),
                'country': store.get('country'),
                'lat': lat,
                'lon': lon,
            }

            yield GeojsonPointItem(**properties)
