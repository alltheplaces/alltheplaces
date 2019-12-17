import json
import scrapy

from locations.items import GeojsonPointItem


class CoopFoodSpider(scrapy.Spider):
    name = "coopfood"
    item_attributes = { 'brand': "Co-op Food" }
    allowed_domains = ["api.coop.co.uk"]
    download_delay = 0.5
    page_number = 1
    start_urls = (
        'https://api.coop.co.uk/locationservices/finder/food/?location=54.9966124%2C-7.308574799999974&distance=30000000000&always_one=true&format=json',
    )

    def parse(self, response):
        data = json.loads(response.body_as_unicode())

        for store in data['results']:
            open_hours = store['opening_hours']
            clean_hours = ''
            for time in open_hours:
                if time['opens'] is not None and time['closes'] is not None:
                    clean_hours = clean_hours + time['name'][:2] + ' ' + time['opens'] + '-' + time['closes'] + ' ; '

            properties = {
                "ref": store['url'],
                "name": store['name'],
                "opening_hours": clean_hours,
                "website": "https://finder.coop.co.uk"+store['url'],
                "addr_full": store['street_address'] + " " + store['street_address2'] + " " + store['street_address3'],
                "city": store['town'],
                "postcode": store['postcode'],
                "country": 'United Kingdom',
                "lon": float(store['position']['x']),
                "lat": float(store['position']['y']),
                "phone": store["phone"],
            }

            yield GeojsonPointItem(**properties)

        if data['next'] is not None:
            self.page_number = self.page_number + 1
            yield scrapy.Request(
                self.start_urls[0] + '&page=' + str(self.page_number)
            )
