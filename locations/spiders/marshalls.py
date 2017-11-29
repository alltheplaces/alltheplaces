import scrapy
import json
from locations.items import GeojsonPointItem

STATES = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DC", "DE", "FL", "GA",
          "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
          "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
          "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
          "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"]

URL = 'https://mktsvc.tjx.com/storelocator/GetSearchResultsByState'


class MarshallsSpider(scrapy.Spider):

    name = "marshalls"
    allowed_domains = ["mktsvc.tjx.com", 'www.marshallsonline.com']

    def start_requests(self):
        url = URL

        headers = {
                   'Accept-Language': 'en-US,en;q=0.8,ru;q=0.6',
                   'Origin': 'https://www.marshallsonline.com',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Accept': 'application/json, text/plain, */*',
                   'Referer': 'https://www.marshallsonline.com/store-finder/by-state',
                   'Connection': 'keep-alive',
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   }

        for state in STATES:
            form_data = {'chain': '10', 'lang': 'en', 'state': state}

            yield scrapy.http.FormRequest(url=url, method='POST', formdata=form_data,
                                          headers=headers, callback=self.parse)

    def parse(self, response):
        data = json.loads(response.text)
        stores = data.get('Stores', None)

        for store in stores:
            lon_lat = [store.pop('Longitude', None), store.pop('Latitude', None)]
            store['ref'] = URL

            yield GeojsonPointItem(
                properties=store,
                lon_lat=lon_lat
            )
