# -*- coding: utf-8 -*-
import scrapy
import json

from locations.items import GeojsonPointItem

class AramarkSpider(scrapy.Spider):
    name = "aramark"
    item_attributes = {'brand': "Aramark"}
    allowed_domains = [
        "www.aramark.com",
        "www.aramarkuniform.com"]
    start_urls = (
        'https://www.aramarkuniform.com/our-locations#',
    )

    def start_requests(self):
        template = 'https://www.aramarkuniform.com/ausgetlocations?zip=&city='

        headers = {
            'Accept': 'application/json',
        }

        yield scrapy.http.FormRequest(
            url=template,
            method='GET',
            headers=headers,
            callback=self.parse
        )

    def parse(self, response):
        base_url = 'https://www.aramarkuniform.com'
        jsonresponse = json.loads(response.body_as_unicode())
        stores = jsonresponse['results']
        for store in stores:
            try:
                properties = {
                    'ref': store["title"],
                    'addr_full': store["streetAddress"],
                    'city': store["locality"],
                    'state': store["region"]["short"],
                    'postcode': store["postalCode"],
                    'phone': store["phone"],
                    'lat': float(store["lat"]),
                    'lon': float(store["lng"]),
                    'website': base_url + store["url"]
                }
            except:
                continue
            yield GeojsonPointItem(**properties)
