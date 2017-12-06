import json
import re
import scrapy
from locations.items import GeojsonPointItem


class TopsSpider(scrapy.Spider):
    name = "tops"
    allowed_domains = ["www.topsmarkets.com"]

    url = 'http://www.topsmarkets.com/StoreLocator/Store_MapDistance_S.las?miles=1000&zipcode='
    available_urls = []

    zipcodes = ['83253', '57638', '54848', '44333', '03244', '23435', '31023', '38915', '79525', '81321', '89135', '98250', 
                '69154', '62838', '89445', '93204', '59402', '57532', '69030', '65231', '70394', '78550', '32566', '33185',
                '27229', '16933', '41231', '46992']

    for zipcode in zipcodes:
        available_urls.append(url + zipcode)

    start_urls = tuple(available_urls)

    def parse(self, response):
        try:
            data = json.loads(response.body_as_unicode())
        except ValueError:
            return
        for item in data:
            properties = {
                'ref': item['StoreNbr'],
                'lat': item['Latitude'],
                'lon': item['Longitude'],
            }

            yield GeojsonPointItem(**properties)

