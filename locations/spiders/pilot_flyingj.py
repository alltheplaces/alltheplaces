import json

import scrapy
from locations.items import GeojsonPointItem


class PilotFlyingJSpider(scrapy.Spider):
    name = "pilot_flyingj"
    brand = "Pilot Flying J"
    download_delay = 0.3
    allowed_domains = [
        "pilotflyingj.com",
    ]
    headers = {'Content-Type': 'application/json'}

    def start_requests(self):
        payload = {
                "PageNumber": 1,
                "PageSize": 50,
                "States": [],
                "Countries": [],
                "Concepts": []
            }
        return [scrapy.Request("https://pilotflyingj.com/umbraco/surface/storelocations/search",
                               method='POST',
                               body=json.dumps(payload),
                               headers=self.headers,
                               callback=self.parse)]

    def parse_store(self, response):
        properties = response.meta["properties"]

        lat = response.xpath('//ul[@id="places-in-map"]/@data-lat').extract()
        long = response.xpath('//ul[@id="places-in-map"]/@data-long').extract()

        properties.update({
            'name': response.xpath('//h1[@class="store-name"]/text()').extract_first().strip(),
            'website': response.url,
            'lat':  float(lat[0]),
            'lon':  float(long[0]),
            'extras': {
                'number': properties["ref"]
            }
        })

        yield GeojsonPointItem(**properties)

    def parse(self, response):

        data = json.loads(response.body_as_unicode())
        current_page_number = data["PageNumber"]
        total_pages = data["TotalPages"]

        stores = data.get("Locations", [])

        if current_page_number <= total_pages:
            for store in stores:
                properties = {
                    'addr_full': store["StreetAddress"].strip(),
                    'city': store['City'].strip(),
                    'state': store['State'].strip(),
                    'postcode': store['ZipCode'].strip(),
                    'phone': store["PhoneNumber"].strip(),
                    'ref': store['StoreNumber'],
                }
                yield scrapy.Request('https://pilotflyingj.com/stores/{}/'.format(store["Id"]),
                                     callback=self.parse_store,
                                     meta={'properties': properties})

            payload = {
                "PageNumber": current_page_number + 1,
                "PageSize": 50,
                "States": [],
                "Countries": [],
                "Concepts": []
            }
            yield scrapy.Request("https://pilotflyingj.com/umbraco/surface/storelocations/search",
                                 method='POST',
                                 body=json.dumps(payload),
                                 headers=self.headers,
                                 callback=self.parse)
