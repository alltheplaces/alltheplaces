import scrapy
from locations.items import GeojsonPointItem
import json


class LushSpider(scrapy.Spider):
    name = 'lush'
    download_delay = 0
    allowed_domains = ['www.lushusa.com', 'lush.ca']
    start_urls = [
        'https://www.lushusa.com/on/demandware.store/Sites-Lush-Site/default/Stores-FindStores?showMap=false&radius=50000&postalCode=78704',
        'https://www.lush.ca/on/demandware.store/Sites-LushCA-Site/en_CA/Stores-FindStores?showMap=false&radius=50000&postalCode=V5K%200A1'
    ]

    def parse(self, response):
        results = json.loads(response.body_as_unicode())
        for i in results["stores"]:
            yield GeojsonPointItem(
                ref=i['ID'],
                name=i['name'],
                phone=i.get('phone'),
                addr_full=i['address1'],
                postcode=i['postalCode'],
                city=i['city'],
                state=i['stateCode'],
                country=i['countryCode'] or 'US',
                lat=i['latitude'],
                lon=i['longitude'],
            )
