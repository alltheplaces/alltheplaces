import json

import scrapy

from locations.hours import OpeningHours
from locations.items import GeojsonPointItem




class BaptistHealthSpider(scrapy.Spider):
    name = "bha"
    allowed_domains = ['algolia.net', 'baptist-health.com']
    start_urls = ['https://www.baptist-health.com/healthcare-arkansas-locations/']
    #download_delay =

    def parse(self, response):
        url = 'https://6eh1ib012d-dsn.algolia.net/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(3.33.0)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(3.6.0)%3B%20Vue%20(2.6.10)%3B%20Vue%20InstantSearch%20(2.3.0)%3B%20JS%20Helper%20(2.28.0)&x-algolia-application-id=6EH1IB012D&x-algolia-api-key=66eafc59867885378e0a81317ea35987'

        payload = '{"requests":[{"indexName":"wp_posts_location","params":"query=&hitsPerPage=500&maxValuesPerFacet=150&page=0&facets=%5B%22city%22%2C%22facility_type%22%5D&tagFilters="}]}'

        headers = {
            'accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'content-type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.baptist-health.com',
            'Referer': 'https://www.baptist-health.com/',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36',
        }

        yield scrapy.http.FormRequest(url=url, method='POST', body=payload, headers=headers,
                                      callback=self.parse_stores)

    def parse_stores(self, response):
        data = json.dumps(json.loads(response.text), sort_keys=True)
        data2 = data.split('"post_title": "')
        for i in data2[1:]:
            for j in i.split(', '):
                if j.split(': "')[0].strip('"') == 'address_1':
                    add1 = j.split(': "')[1].strip('"')
                elif j.split(': "')[0].strip('"') == 'address_2':
                    add2 = j.split(': "')[1].strip('"')
                elif j.split(': "')[0].strip('"') == 'city':
                    city = j.split(': "')[1].strip('"')
                elif j.split(': "')[0].strip('"') == 'state':
                    state = j.split(': "')[1].strip('"')
                elif j.split(': "')[0].strip('"}') == 'zip_code':
                    pc = j.split(': "')[1].strip('"')
                elif j.split(': "')[0].strip('"') == 'phone_number':
                    phone = j.split(': "')[1].strip('"')
                elif j.split(': ')[0].strip('"') == '{"_geoloc':
                    lat = float(j.split(': ')[2].strip('}'))
                elif j.split(': ')[0].strip('"') == 'lng':
                    lng = float(j.split(': ')[1].strip('}'))
                elif j.split(': "')[0].strip('"') == 'permalink':
                    ref = j.split(': "')[1].strip('"')
                else:
                    pass

            properties = {
                'name': "Baptist Health Arkansas",
                'ref': ref,
                'addr_full': add1 + ', ' + add2,
                'city': city,
                'state': state,
                'postcode': pc,
                'country': "US",
                'phone': phone,
                'lat': lat,
                'lon': lng,
            }
            yield GeojsonPointItem(**properties)